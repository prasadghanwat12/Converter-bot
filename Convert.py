import os
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import tempfile

# Ensure the bot token is taken from the environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Bot token not set. Please set the BOT_TOKEN environment variable.")

# Function to check and install Calibre with additional dependencies
def check_and_install_calibre():
    try:
        subprocess.run(["ebook-convert", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Calibre is already installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Calibre is not installed. Installing...")

        # Suppress output during installation
        with open(os.devnull, 'wb') as devnull:
            subprocess.run(["sudo", "apt", "update"], check=True, stdout=devnull, stderr=devnull)
            subprocess.run([
                "sudo", "apt", "install", "-y", "wget", "xdg-utils", "python3", "lsof",
                "libfontconfig1", "libfreetype6", "libxcb-cursor0", "libxkbfile1",  # Added libxkbfile1 dependency
                "libx11-xcb1", "libxcb1", "libxcb-render0", "libxcb-shm0",
                "libxcb-xfixes0", "libjpeg8", "libpng16-16", "libglib2.0-0",
                "libxrender1", "libxext6", "libxcomposite1", "libxi6", "libxtst6",
                "libxslt1.1", "libxrandr2", "libcups2", "libdbus-1-3", "libexpat1",
                "libuuid1", "liblzma5", "zlib1g", "libqt5webkit5",  # Added libqt5webkit5 dependency
                "qt5-qmake", "qtbase5-dev"  # Added additional Qt libraries
            ], check=True, stdout=devnull, stderr=devnull)

            subprocess.run(["wget", "-nv", "https://download.calibre-ebook.com/linux-installer.sh"], check=True, stdout=devnull, stderr=devnull)
            subprocess.run(["sudo", "sh", "linux-installer.sh"], check=True, stdout=devnull, stderr=devnull)

        try:
            subprocess.run(["calibre", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Calibre installation successful.")
        except subprocess.CalledProcessError:
            print("Calibre installation failed.")

# Conversion function
def convert_file(input_file_path, output_file_path):
    try:
        subprocess.run(["ebook-convert", input_file_path, output_file_path], check=True)
        print("Conversion successful.")
    except subprocess.CalledProcessError as e:
        print("Conversion failed:", e)

# Command handler for /convert
async def convert_command(update: Update, context: CallbackContext) -> None:
    if update.message.reply_to_message and update.message.reply_to_message.document:
        document = update.message.reply_to_message.document
        file_name = document.file_name

        if file_name.endswith(".epub") or file_name.endswith(".pdf"):
            # Download the file
            file = await context.bot.get_file(document.file_id)
            file_bytes = await file.download_as_bytearray()

            # Save to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".epub" if file_name.endswith(".epub") else ".pdf") as temp_input:
                temp_input.write(file_bytes)
                temp_input_path = temp_input.name

            # Determine output path and format
            output_extension = ".pdf" if file_name.endswith(".epub") else ".epub"
            temp_output_path = temp_input_path.replace(".epub", ".pdf") if file_name.endswith(".epub") else temp_input_path.replace(".pdf", ".epub")

            # Convert file format
            convert_file(temp_input_path, temp_output_path)

            # Check if output file exists before attempting to send
            if os.path.exists(temp_output_path):
                with open(temp_output_path, "rb") as converted_file:
                    await context.bot.send_document(
                        chat_id=update.message.chat_id,
                        document=converted_file,
                        reply_to_message_id=update.message.reply_to_message.message_id,
                        caption="Here's your converted file!"
                    )

                # Clean up temporary files
                os.remove(temp_input_path)
                os.remove(temp_output_path)
            else:
                await update.message.reply_text("Conversion failed. Please try again.")
        else:
            await update.message.reply_text("Please reply to a .epub or .pdf file to convert.")
    else:
        await update.message.reply_text("Please reply to a .epub or .pdf file to convert.")

# Main function to set up the bot
def main():
    # Check and install Calibre if not installed
    check_and_install_calibre()

    # Initialize the bot
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handler for /convert
    application.add_handler(CommandHandler("convert", convert_command))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
