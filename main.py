import telebot
import json
import logging

logging.basicConfig(
    filename='log.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def register_chat(message_thread_id, chat_id_sender):
    with open("chat_ids.json", "r") as d:
        data = json.load(d)
    data[str(chat_id_sender)] = message_thread_id 
    with open("chat_ids.json", "w") as d:
        json.dump(data, d, indent=4)

with open("config.json", "r") as d:
    config_data = json.load(d)
with open("chat_ids.json", "r") as d:
    chat_ids = json.load(d)

bot = telebot.TeleBot(config_data["token"])

@bot.message_handler(func=lambda message: True, content_types=['audio', 'photo', 'voice', 'video', 'document',
    'text', 'location', 'contact', 'sticker'])
def message_get(message):
    user_id = str(message.from_user.id)

    if user_id in chat_ids:
        topic_id = chat_ids[user_id]
        if user_id in config_data["blacklist"]:
            bot.send_message(config_data["forum_id"], message_thread_id=topic_id, text=f"User {user_id} blocked")
            return
        bot.send_message(chat_id=config_data["forum_id"], message_thread_id=topic_id, text=message.text)
        return

    if user_id in config_data["blacklist"]:
        bot.reply_to(message, config_data["blocked_message"])
        return

    if config_data["forum_id"] == 0:
        bot.reply_to(message, "Bot is not configured, cant send message...")
        return

    bot.reply_to(message, config_data["message_send_wait"])
    username = message.from_user.username
    first_name = message.from_user.first_name
    topic = bot.create_forum_topic(chat_id=config_data["forum_id"], name=f"{first_name} - @{username}")
    bot.send_message(chat_id=config_data["forum_id"], message_thread_id=topic.message_thread_id,
                     text=f"Chat created for @{username} - {first_name}")
    bot.send_message(chat_id=config_data["forum_id"], message_thread_id=topic.message_thread_id, text=message.text)
    register_chat(topic.message_thread_id, user_id)
    bot.reply_to(message, text=config_data["message_send"])
    logger.info("New chat succesfully registered!")

    if message.message_thread_id:
        target_user_id = None
        for uid, tid in chat_ids.items():
            if tid == message.message_thread_id:
                target_user_id = uid
                break
        if target_user_id:
            text_lower = message.text.lower() if message.text else ""
            if text_lower.startswith("/blacklist"):
                if target_user_id not in config_data["blacklist"]:
                    config_data["blacklist"].append(target_user_id)
                try:
                    bot.close_forum_topic(chat_id=config_data["forum_id"], message_thread_id=message.message_thread_id)
                except Exception as e:
                    logger.error(f"Error closing topic {message.message_thread_id}: {e}")
                bot.send_message(target_user_id, config_data["blocked_message"])
                bot.send_message(config_data["forum_id"], message.message_thread_id, f"User {target_user_id} добавлен в blacklist ✅")
                return
            elif text_lower.startswith("/unblacklist"):
                if target_user_id in config_data["blacklist"]:
                    config_data["blacklist"].remove(target_user_id)
                bot.send_message(target_user_id, config_data["unblocked_message"])
                bot.send_message(config_data["forum_id"], message.message_thread_id, f"User {target_user_id} unblocked")
                return
            else:
                if target_user_id in config_data["blacklist"]:
                    bot.send_message(config_data["forum_id"], message.message_thread_id, f"User {target_user_id} blocked")
                    return
                bot.send_message(target_user_id, message.text)
                return

if __name__ == '__main__':
    logger.info("Starting bot...")
    bot.infinity_polling()
