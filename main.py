from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler, CallbackContext, filters
)
from modules.ml_module import MLTrackModule
from modules.ios_module import iOSTrackModule
from rag_manager import RAGManager
from dotenv import load_dotenv
import os
import chromadb
import sqlite3

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Database connection
client = chromadb.HttpClient(host='localhost', port=8000)
chromadb_connection = client.get_or_create_collection(name="chromadb_demo")

# SQLite database connection and table creation
def create_sqlite_db(path):
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS questions (
                        id TEXT PRIMARY KEY,
                        theme TEXT,
                        question TEXT,
                        answer TEXT,
                        level TEXT,
                        status TEXT)''')
    connection.commit()
    return connection

# Create or open SQLite database
db_path = 'sglite_demo.db'
sqlite_connection = create_sqlite_db(db_path)

rag_manager = RAGManager(chromadb_connection, sqlite_connection)

# Define states for conversation
CHOOSING_TRACK, CHOOSING_LEVEL, CHOOSING_QUESTIONS, THEME_OPTION, GENERATE_TEST, GENERATE_REPORT, RETAKE_TEST = range(7)

# Global variables to store user preferences
user_preferences = {}

# Command handler for '/start'
async def start(update: Update, context: CallbackContext):
    print("Starting conversation...")
    await update.message.reply_text(
        "Welcome to the Interview Bot! Please choose a track:\n\n"
        "1. ML_EN\n"
        "2. IOS_RU", 
        reply_markup=ReplyKeyboardMarkup([['ML_EN', 'IOS_RU']], one_time_keyboard=True)
    )
    return CHOOSING_TRACK

# Track selection handler
async def choose_track(update: Update, context: CallbackContext):
    user_preferences['track'] = update.message.text
    print(f"Track selected: {user_preferences['track']}")
    
    if user_preferences['track'] == 'ML_EN':
        print("Sending ML_EN track level options...")
        await update.message.reply_text(
            "Please choose your level:\n\n"
            "1. Junior\n"
            "2. Middle/Senior\n"
            "3. Deep Learning\n"
            "4. NLP",
            reply_markup=ReplyKeyboardMarkup([['Junior', 'Middle/Senior', 'Deep_Learning', 'NLP']], one_time_keyboard=True)
        )
    else:  # For iOS
        print("Sending iOS_RU track level options...")
        await update.message.reply_text(
            "Please choose your level:\n\n"
            "1. Junior\n"
            "2. Middle\n"
            "3. Senior",
            reply_markup=ReplyKeyboardMarkup([['Junior', 'Middle', 'Senior']], one_time_keyboard=True)
        )
    return CHOOSING_LEVEL

# Level selection handler
async def choose_level(update: Update, context: CallbackContext):
    user_preferences['level'] = update.message.text
    print(f"Level selected: {user_preferences['level']}")
    await update.message.reply_text(
        "How many questions would you like? (3, 5, 10)",
        reply_markup=ReplyKeyboardMarkup([['3', '5', '10']], one_time_keyboard=True)
    )
    return CHOOSING_QUESTIONS
    
async def choose_questions(update: Update, context: CallbackContext):
    try:
        user_preferences['number_of_questions'] = int(update.message.text)
        print(f"Number of questions selected: {user_preferences['number_of_questions']}")

        # Provide the user with options for the next step
        await update.message.reply_text(
            "Would you like to:\n"
            "1. Choose a specific theme\n"
            "2. Generate questions automatically",
            reply_markup=ReplyKeyboardMarkup([['Choose theme', 'Generate questions']], one_time_keyboard=True)
        )
        return THEME_OPTION
    except ValueError:
        await update.message.reply_text("Please enter a valid number for the number of questions.")
        return CHOOSING_QUESTIONS

# Theme option handler
async def theme_option(update: Update, context: CallbackContext):
    user_choice = update.message.text
    
    if user_choice == 'Choose theme':
        await update.message.reply_text("Please enter the theme you want to focus on:")
        return THEME_OPTION  # Move to a state where the bot expects theme input

    elif user_choice == 'Generate questions':
        user_preferences['theme'] = None  # No specific theme selected
        print("No specific theme chosen. Proceeding with questions by level.")
        return await generate_test(update, context)  # Directly call the function to generate the test

    else:
        # User entered a theme
        user_preferences['theme'] = user_choice
        print(f"User chosen theme: {user_preferences['theme']}")
        return await generate_test(update, context)

# Function to generate the test
async def generate_test(update: Update, context: CallbackContext):
    print("Generating test...")

    if user_preferences['track'] == 'ML_EN':
        print("Initializing ML module...")
        module = MLTrackModule(user_preferences, rag_manager)
    else:
        print("Initializing iOS module...")
        module = iOSTrackModule(user_preferences, rag_manager)

    # Fetch questions based on user preferences (level and theme)
    if user_preferences['theme']:
        questions = module.get_questions_by_theme()
    else:
        questions = module.get_questions_by_level()
    
    user_preferences['questions'] = questions

    # Create a single string to hold the test content
    test_content = "Here's your test:\n\n"
    idx = 1
    print(questions)
    for question in questions[:user_preferences['number_of_questions']]:
        test_content += f"{idx}. {question['question']}\n\n"
        idx += 1
    # Send the complete test in one message
    await update.message.reply_text(test_content)

    await update.message.reply_text("Test generation complete. Good luck! \n Please, write your answers in single message and send!")

    return GENERATE_REPORT

# Final Report option handler
async def generate_report(update: Update, context: CallbackContext):
    user_answers = update.message.text.lower()
    if user_preferences['track'] == 'ML_EN':
        module = MLTrackModule(user_preferences, rag_manager)
    else:
        module = iOSTrackModule(user_preferences, rag_manager)
    report_prompt = await module.generate_report(user_answers, user_preferences['questions'])
    await update.message.reply_text(report_prompt)
    
    # Ask if the user wants to retake the test with buttons
    reply_keyboard = [['Yes', 'No']]
    await update.message.reply_text(
        "Would you like to take the new test? (yes/no)",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return RETAKE_TEST

# Retake test handler
async def retake_test(update: Update, context: CallbackContext):
    user_response = update.message.text.lower()

    if user_response == 'yes':
        # Reset user preferences to start over
        user_preferences.clear()
        await update.message.reply_text(
            "Let's start a new test! Please choose a track:\n\n"
            "1. ML_EN\n"
            "2. IOS_RU",
            reply_markup=ReplyKeyboardMarkup([['ML_EN', 'IOS_RU']], one_time_keyboard=True, resize_keyboard=True)
        )
        return CHOOSING_TRACK
    elif user_response == 'no':
        # Provide a "Start Again" button along with a goodbye message
        reply_keyboard = [['Start Again']]
        await update.message.reply_text(
            "Thank you for using the Interview Bot! If you'd like to start again, press the button below.",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return RETAKE_TEST
    elif user_response == 'start again':
        # Reset user preferences and go back to track selection
        user_preferences.clear()
        await update.message.reply_text(
            "Let's start a new test! Please choose a track:\n\n"
            "1. ML_EN\n"
            "2. IOS_RU",
            reply_markup=ReplyKeyboardMarkup([['ML_EN', 'IOS_RU']], one_time_keyboard=True, resize_keyboard=True)
        )
        return CHOOSING_TRACK
    else:
        await update.message.reply_text("Thank you for using the Interview Bot! Goodbye.")
        return ConversationHandler.END
    
# Conversation handler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        CHOOSING_TRACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_track)],
        CHOOSING_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_level)],
        CHOOSING_QUESTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_questions)],
        THEME_OPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, theme_option)],
        GENERATE_TEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_test)],
        GENERATE_REPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_report)],
        RETAKE_TEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, retake_test)],
    },
    fallbacks=[],
)

# Build the application
app = Application.builder().token(TOKEN).build()

# Add handlers
app.add_handler(conv_handler)

# Run the bot
app.run_polling()