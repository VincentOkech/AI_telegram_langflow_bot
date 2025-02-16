#!/usr/bin/env python
import logging
import json
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
import requests

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# States
ASKING = 0

# Langflow Configuration
BASE_API_URL = "https://api.langflow.astra.datastax.com"
LANGFLOW_ID = "979f2f1f-2249-4fdbdd359621"
ENDPOINT = "Customer"  # The endpoint name of the flow
APPLICATION_TOKEN = "AstraCS:BoUWqZqQt:4d34b7f7550a12e68e97491e838776adb77c2e9504e219dac3da5c899bca80b4"
TELEGRAM_TOKEN = "7867905932:AAFAGA-p-AprhhIfJSjZ548"

# Default tweaks from your API configuration
TWEAKS = {
    "ChatInput-eJrW0": {},
    "Prompt-eIEV4": {},
    "AstraDB-KgyGC": {},
    "ParseData-7MHJe": {},
    "File-LYwDl": {},
    "SplitText-tlHcr": {},
    "AstraDB-IlnAL": {},
    "ChatOutput-QWjU8": {},
    "Agent-bGEER": {},
    "Agent-xaG2M": {},
    "DuckDuckGoSearch-zCOJ2": {}
}

async def run_flow(message: str) -> dict:
    """Run the Langflow with the given message."""
    api_url = f"{BASE_API_URL}/lf/{LANGFLOW_ID}/api/v1/run/{ENDPOINT}"
    
    payload = {
        "input_value": message,
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": TWEAKS
    }
    
    headers = {
        "Authorization": f"Bearer {APPLICATION_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return {"error": str(e)}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation."""
    await update.message.reply_text(
        "Hello! I'm your AI assistant powered by Langflow. "
        "You can ask me anything, and I'll try to help. "
        "Send /cancel to stop the conversation."
    )
    return ASKING

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user messages and forward them to Langflow."""
    user_message = update.message.text
    user = update.message.from_user
    logger.info(f"Message from {user.first_name}: {user_message}")
    
    try:
        # Call Langflow API
        result = await run_flow(user_message)
        
        if "error" in result:
            await update.message.reply_text(
                "Sorry, there was an error connecting to the AI service. Please try again later."
            )
            return ASKING
            
        # Extract response from the result
        ai_response = result.get("response", result.get("output", "I couldn't process that properly."))
        
        await update.message.reply_text(str(ai_response))
        return ASKING
        
    except Exception as e:
        logger.error(f"Error while calling Langflow API: {e}")
        await update.message.reply_text(
            "Sorry, I encountered an error while processing your request. "
            "Please try again later."
        )
        return ASKING

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and ends the conversation."""
    user = update.message.from_user
    logger.info(f"User {user.first_name} canceled the conversation.")
    await update.message.reply_text(
        "Goodbye! Feel free to start a new conversation anytime with /start",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    print("Bot is starting up...")
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()