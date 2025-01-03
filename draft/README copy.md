# Diets and Calisthenics Telegram Bot

This is a simple Telegram bot that provides information about diets and calisthenics using Gemini LLM API. The bot asks the user for their weight, height, and age before answering any questions.

### Prerequisites

- Python 3.x

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://gitlab.pg.innopolis.university/llm-course/n.salikhova.git

2. Go into week1 repo
   ```bash
   cd week1

3. Set up virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`

4. Install the required Python packages:
   ```bash
   pip install -r requirements.txt

4) Create a .env file in the root directory of your project with the following content:
   ```bash
   TELEGRAM_TOKEN=your_telegram_bot_token
   GEMINI_API_KEY=your_gemini_api_key

•	For the TELEGRAM_TOKEN, contact @BotFather on Telegram to create a new bot and obtain the token.

•	For the GEMINI_API_KEY, visit [Google AI Studio](https://aistudio.google.com) to generate an API key.

5) Start the bot by running the following command:
   ```bash
   python bot.py
