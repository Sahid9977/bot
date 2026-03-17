import os
import telebot
from flask import Flask, request
from openai import OpenAI

# 1. Fetch Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")
# Render automatically provides this environment variable (e.g., https://your-app.onrender.com)
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL") 

# Ensure tokens are provided
if not BOT_TOKEN or not HF_TOKEN:
    raise ValueError("BOT_TOKEN and HF_TOKEN must be set in environment variables.")

# 2. Initialize Telegram Bot and Flask App
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 3. Initialize OpenAI Client (Pointed to Hugging Face)
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# 4. Handle /start and /help commands
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hello! I am an AI chatbot powered by DeepSeek-R1. Send me a message and I'll reply!")

# 5. Handle all other text messages
@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    try:
        # Show "typing..." action in Telegram
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Call Hugging Face API
        chat_completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1:novita",
            messages=[
                {
                    "role": "user",
                    "content": message.text,
                }
            ],
        )
        
        # Extract the AI's response and send it back to the user
        reply_text = chat_completion.choices[0].message.content
        bot.reply_to(message, reply_text)
        
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Sorry, I encountered an error while thinking. Please try again later.")

# 6. Flask route to receive webhooks from Telegram
@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

# 7. Flask route for Render health checks and Webhook setup
@app.route('/')
def webhook():
    return "Bot is running!", 200

if __name__ == "__main__":
    # If running on Render, set up the webhook and run Flask
    if RENDER_EXTERNAL_URL:
        bot.remove_webhook()
        # Set the webhook URL to the Render app URL + the bot token
        webhook_url = f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
        bot.set_webhook(url=webhook_url)
        
        # Render sets the PORT environment variable automatically
        port = int(os.environ.get('PORT', 5000))
        app.run(host="0.0.0.0", port=port)
    else:
        # Local testing fallback (Polling instead of Webhooks)
        bot.remove_webhook()
        print("Bot started in polling mode...")
        bot.infinity_polling()
