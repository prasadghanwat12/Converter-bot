import os
import tempfile
import pypandoc
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging
import subprocess

# Ensure Calibre is installed or install it
def check_and_install_calibre():
    try:
        subprocess.run(["ebook-convert", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("Calibre not found, installing...")
        subprocess.run("sudo apt update", shell=True)
        subprocess.run("sudo apt install -y wget xdg-utils python3 lsof libfontconfig1 libfreetype6 libxcb-cursor0", shell=True)
        subprocess.run("sudo apt install -y libx11-xcb1 libxcb1 libxcb-render0 libxcb-shm0 libxcb-xfixes0 libjpeg8 libpng16-16 libglib2.0-0 libxrender1 libxext6 libxcomposite1 libxi6 libxtst6 libxslt1.1 libxrandr2 libcups2 libdbus-1-3 libexpat1 libuuid1 liblzma5 zlib1g", shell=True)
        subprocess.run("wget -nv https://download.calibre-ebook.com/linux-installer.sh", shell=True)
        subprocess.run("sudo sh linux-installer.sh", shell=True)
        print("Calibre installation successful.")

# Function to convert files using pypandoc as an alternative
def convert_file(input_file_path, output_file_path):
    try:
        pypandoc.convert_file(input_file_path, 'pdf' if input_file_path.endswith('.epub') else 'epub', outputfile=output_file_path)
        print("Conversion successful.")
    except Exception as e:
        print("Conversion failed:", e)

async def convert_command(update: Update, context):
    check_and_install_calibre()
    
    if not update.message or not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("Please reply to an EPUB or PDF file with /convert to convert it.")
        return

    # Get file info and check format
    document = update.message.reply_to_message.document
    file_name, file_extension = os.path.splitext(document.file_name)
    if file_extension.lower() not in ['.epub', '.pdf']:
        await update.message.reply_text("Unsupported file format. Only EPUB and PDF files are supported.")
        return

    # Download the file
    file = await document.get_file()
    temp_input_path = tempfile.mktemp(suffix=file_extension)
    await file.download_to_drive(temp_input_path)

    # Define the output file path with the same base name but converted extension
    output_extension = '.pdf' if file_extension.lower() == '.epub' else '.epub'
    temp_output_path = os.path.join(tempfile.gettempdir(), f"{file_name}{output_extension}")

    # Convert the file
    convert_file(temp_input_path, temp_output_path)

    # Send the converted file back
    try:
        with open(temp_output_path, "rb") as converted_file:
            await update.message.reply_document(converted_file, filename=os.path.basename(temp_output_path), caption="Here's your converted file.")
    except FileNotFoundError:
        await update.message.reply_text("Conversion failed. Please try again.")

    # Clean up temp files
    os.remove(temp_input_path)
    os.remove(temp_output_path)

async def start(update: Update, context):
    await update.message.reply_text("Hello! Reply to a file with /convert to convert between EPUB and PDF formats.")

if __name__ == "__main__":
    import os
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("convert", convert_command))

    print("Bot is running...")
    application.run_polling()
