import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import requests
from bs4 import BeautifulSoup

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram bot token from environment variable
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Subtitle download URL
SUBTITLE_URL = "https://www.opensubtitles.org"

# User agent for making requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"

def start(update: Update, context):
    """Handler for /start command"""
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Welcome to the Subtitle Bot!\nSend me the name of a movie or TV show and I will try to find the subtitles for it.")

def search_subtitles(update: Update, context):
    """Handler for searching and displaying subtitles"""
    search_query = update.message.text

    # Send a typing action while searching for subtitles
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action="TYPING")

    # Search for subtitles
    subtitles = find_subtitles(search_query)

    if subtitles:
        # Create an InlineKeyboardMarkup with download buttons for each subtitle
        keyboard = []
        for subtitle in subtitles:
            title = subtitle["title"]
            link = subtitle["link"]
            button = InlineKeyboardButton(text=title, url=link)
            keyboard.append([button])

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the found subtitles with download buttons
        context.bot.send_message(chat_id=update.effective_chat.id, text="Found Subtitles:")
        context.bot.send_message(chat_id=update.effective_chat.id, text="Click the download button to download the subtitle.",
                                 reply_markup=reply_markup)
    else:
        # Send a message if no subtitles are found
        context.bot.send_message(chat_id=update.effective_chat.id, text="No subtitles found for this query.")

def find_subtitles(search_query):
    """Search for subtitles using the search query"""
    headers = {
        "User-Agent": USER_AGENT,
    }

    search_url = f"{SUBTITLE_URL}/en/search/sublanguageid-all/moviename-{search_query}"

    # Make a request to the search URL
    response = requests.get(search_url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        subtitle_items = soup.find_all("div", class_="botttomSearch")
        subtitles = []

        for item in subtitle_items:
            title = item.find("a").get("title")
            link = f"{SUBTITLE_URL}{item.find('a').get('href')}"
            subtitles.append({"title": title, "link": link})

        return subtitles

    return None

def error(update: Update, context):
    """Log errors"""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    """Main function to start the bot"""
    # Create the Updater and pass in the bot's token
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))

    # Register message handler for searching subtitles
    dispatcher.add_handler(MessageHandler(Filters.text, search_subtitles))

    # Register callback query handler for download buttons
    dispatcher.add_handler(CallbackQueryHandler(download_subtitle))

    # Register error handler
    dispatcher.add_error_handler(error)

    # Start the bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()
