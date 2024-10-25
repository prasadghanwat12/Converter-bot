import os
import subprocess
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Telegram Bot Token
BOT_TOKEN = '7608853349:AAH5SzDCIpTbmWCUxxseXH05zk5zkEkGZOo'

# Function to check and install Calibre if not installed
def check_and_install_calibre():
    try:
        # Check if Calibre's `ebook-convert` command is available
        subprocess.run(["ebook-convert", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("Calibre is not installed. Installing...")
        # Install Calibre (Debian-based example)
        subprocess.run(["sudo", "apt", "update"])
        subprocess.run(["sudo", "apt", "install", "-y", "calibre"])

# Function to convert file using Calibre
def convert_file(file_path, output_format):
    base, _ = os.path.splitext(file_path)
    output_path = f"{base}.{output_format}"
    command = [
        "ebook-convert",
        file_path,
        output_path,
        "--embed-font-family",
        "serif"
    ]
    try:
        subprocess.run(command, check=True)
        return output_path
    except subprocess.CalledProcessError:
        return None

# Handler for the /convert command
def convert_handler(update: Update, context: CallbackContext):
    message = update.message
    if message.reply_to_message and message.reply_to_message.document:
        file = message.reply_to_message.document
        file_name = file.file_name.lower()

        # Check if the file is .epub or .pdf
        if file_name.endswith('.epub'):
            output_format = 'pdf'
        elif file_name.endswith('.pdf'):
            output_format = 'epub'
        else:
            message.reply_text("Please reply to a .epub or .pdf file to convert.")
            return

        # Download the file
        file_path = file.get_file().download(custom_path=file_name)

        # Convert the file
        converted_file_path = convert_file(file_path, output_format)
        
        if converted_file_path:
            # Send the converted file as a reply to the original message
            context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=open(converted_file_path, 'rb'),
                reply_to_message_id=message.reply_to_message.message_id
            )
            os.remove(converted_file_path)
        else:
            message.reply_text("Conversion failed. Please try again.")
        os.remove(file_path)
    else:
        message.reply_text("Please reply to a .epub or .pdf file to convert.")

# Main function to set up the bot
def main():
    # Check and install Calibre if needed
    check_and_install_calibre()

    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add command handler for /convert
    dp.add_handler(CommandHandler("convert", convert_handler))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
