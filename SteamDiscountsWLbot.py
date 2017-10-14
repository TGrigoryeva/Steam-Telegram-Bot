from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import telegram
import logging
from SteamDiscountsWLbot_APIkey import key
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from steam_parser import wishlist_notifications, check_username
import re
from steam_db import db_session, Chat
from datetime import timedelta

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='bot.log'
                    )

def greet_user(bot, update):
    update.message.reply_text("Для просмотра вишлиста отправьте сообщение с юзернеймом из персональной ссылки Steam:\nhttр://steamcommunity.cоm/id/username\n\nДля подписки на уведомления отправьте команду в формате:\n /notification username\n\nИспользуйте /off, чтобы приостановить подписку.") # клавиатура появится сразу после этого сообщения

def wishlist(bot, update):
    user_text = update.message.text.replace(" ","")
    print(user_text)
    if not check_username(user_text):
        update.message.reply_text("Пользователя {} не существует, либо страница скрыта".format(user_text))
    else:
        my_data = wishlist_notifications(user_text,"wishlist")  # тут словарь лежит
        print(my_data)
        telegram_wishlist = "\n".join(map(str,my_data))
        print(telegram_wishlist)
        if not telegram_wishlist:
            update.message.reply_text("У пользователя нет игр в wishlist")
        else:
            update.message.reply_text(telegram_wishlist)
        
def notification(bot, update):
    user_text = update.message.text[13:].replace(" ","")   
    if not check_username(user_text):
        update.message.reply_text("Пользователя {} не существует, либо страница скрыта".format(user_text))
    else:
        tel_chat_id = update.message.chat_id
        tel_first_name = update.message.from_user.first_name
        tel_last_name = update.message.from_user.last_name
        print(tel_chat_id,tel_first_name,tel_last_name)
        db_tel_chat_id = Chat.query.filter(Chat.chat_id == tel_chat_id).first()
        print(db_tel_chat_id)
        if db_tel_chat_id is None:
            db_session.add(Chat(tel_chat_id, tel_first_name, tel_last_name, True, user_text))
            db_session.commit()
            update.message.reply_text("Подписка включена")
        else:
            update.message.reply_text("Для новой подписки отмените предыдущую")

def off(bot, update):
    tel_chat_id = update.message.chat_id
    try:
        row_to_delete = db_session.query(Chat).filter(Chat.chat_id == tel_chat_id).first()
        db_session.delete(row_to_delete)
        update.message.reply_text("Подписка отключена")
        db_session.commit()
    except:
        update.message.reply_text("Что-то пошло не так")
    

def photo(bot, update):
    print ("Got photo")
    update.message.reply_photo("http://a.deviantart.net/avatars/t/o/toddthegreatshow.jpg?4")

def callback_minute(bot, job):
    db_query = Chat.query.all()
    for chat in db_query:
        result = wishlist_notifications(chat.username,"notification")
        print("telegram message: ", result)
        telegram_notification = "\n".join(map(str,result))
        try:
            bot.sendMessage(chat_id = chat.chat_id, text = telegram_notification)
        except:
            pass

def main():
    updater = Updater(key)
    j = updater.job_queue
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", greet_user))
    dp.add_handler(MessageHandler(Filters.text, wishlist))
    dp.add_handler(CommandHandler("notification", notification))
    dp.add_handler(CommandHandler("off", off))
    dp.add_handler(MessageHandler(Filters.photo, photo))
    job_minute = j.run_repeating(callback_minute, interval=60, first=0)
#    job_minute = j.run_repeating(callback_minute, interval = timedelta(hours = 1), first=0)


#    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    # Start the Bot
    updater.start_polling()
    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()

main()