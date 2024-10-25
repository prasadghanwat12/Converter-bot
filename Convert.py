import os
import tempfile
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging

# Function to install Calibre if not already installed
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

# Function to convert files using Calibre's ebook-convert with enhanced styling
def convert_file(input_file_path, output_file_path):
    try:
        # Additional ebook-convert options to improve PDF styling
        options = [
            "ebook-convert", input_file_path, output_file_path,
            "--pdf-page-margin-top", "30",      # Add top margin
            "--pdf-page-margin-bottom", "30",   # Add bottom margin
            "--pdf-default-font-size", "14",    # Set font size
            "--pdf-mono-font-size", "12",       # Set monospaced font size
            "--pdf-sans-family", "Arial",       # Set sans-serif font
            "--pdf-serif-family", "Times New Roman", # Set serif font
            "--pdf-page-breaks-before-chapter", # Add page breaks before each chapter
            "--pdf-header-template", "Page: {page}", # Add header with page number
            "--chapter", "//*[@class='chapter']", # Identify chapters based on class (example)
            "--margin-left", "40",              # Set left margin
            "--margin-right", "40",             # Set right margin
            "--line-height", "150%",            # Improve line spacing
        ]
        subprocess.run(options, check=True)
        print("Conversion successful with enhanced styling.")
    except subprocess.CalledProcessError as e:
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

    # Convert the file with styling options
    convert_file(temp_input_path, temp_output_path)

    # Send the converted file back
    try:
        with open(temp_output_path, "rb") as converted_file:
            await update.message.reply_document(converted_file, filename=os.path.basename(temp_output_path), caption="Here's your converted file with enhanced styling.")
    except FileNotFoundError:
        await update.message.reply_text("Conversion failed. Please try again.")

    # Clean up temp files
    os.remove(temp_input_path)
    os.remove(temp_output_path)

async def start(update: Update, context):
    await update.message.reply_text("Hello! Reply to a file with /convert to convert between EPUB and PDF formats with enhanced styling.")

if __name__ == "__main__":
    import os
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("convert", convert_command))

    print("Bot is running...")
    application.run_polling()
