from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import telegram
import logging
from SteamDiscountsWLbot_APIkey import key
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from steam_parser import wishlist_notifications, check_username, wl_sales
from steam_db import db_session, Chat
from datetime import timedelta

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='bot.log'
                    )

def greet_user(bot, update):
    update.message.reply_text("Для просмотра вишлиста отправьте сообщение с юзернеймом из персональной ссылки Steam:\
                                \nhttр://steamcommunity.cоm/id/username\
                                \n\nДля подписки на уведомления отправьте команду в формате:\n /add username\
                                \nДля просмотра списка игр со скидками из вишлиста:\n /sales username\
                                \n\nИспользуйте /off, чтобы приостановить подписку."
                                )
 
def wishlist(bot, update):
    """ to get user Steam wishlist """
    user_text = update.message.text.replace(" ","")
    print(user_text)
    if not check_username(user_text):
        update.message.reply_text("Пользователя {} не существует, либо страница скрыта".format(user_text))
    else:
        my_data = wishlist_notifications(user_text,"wishlist")
        print(my_data)
        telegram_wishlist = "\n".join(map(str,my_data))
        print(telegram_wishlist)
        if not telegram_wishlist:
            update.message.reply_text("У пользователя нет игр в wishlist")
        else:
            update.message.reply_text(telegram_wishlist)
  
def sales(bot, update):
    """ to get once info about discounts in user wishlist """
    user_text = update.message.text[6:].replace(" ","")
    print(user_text,"test telegram user_text")
    if not check_username(user_text):
        update.message.reply_text("Пользователя {} не существует, либо страница скрыта".format(user_text))
    else:
        user_discounts = wl_sales(user_text) # не возвращает ничего
        print(user_discounts)        
        telegram_wl_sales = "\n".join(map(str,user_discounts))
        print(telegram_wl_sales)
        if not telegram_wl_sales:
            update.message.reply_text("У пользователя нет игр со скидками в wishlist")
        else:
            update.message.reply_text(telegram_wl_sales)
       
def add(bot, update):
    """ subscribe to notifications about new discounts in user Steam wishlist """
    user_text = update.message.text[4:].replace(" ","")       
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
    """ unsubscribe """
    tel_chat_id = update.message.chat_id
    try:
        row_to_delete = db_session.query(Chat).filter(Chat.chat_id == tel_chat_id).first()
        db_session.delete(row_to_delete)
        update.message.reply_text("Подписка отключена")
        db_session.commit()
    except:
        update.message.reply_text("Подписка отсутствует")
    
def photo(bot, update):
    """ picture callback """
    print ("Got photo")
    update.message.reply_photo("http://cs616125.vk.me/v616125058/806a/S6GoMba5mX8.jpg")

def callback_minute(bot, job):
    """ to run job timer """
    db_query = Chat.query.all()
    for chat in db_query:
        result = wishlist_notifications(chat.username,"add")
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
    dp.add_handler(CommandHandler("add", add))
    dp.add_handler(CommandHandler("sales", sales))
    dp.add_handler(CommandHandler("off", off))
    dp.add_handler(MessageHandler(Filters.photo, photo))
#    job_minute = j.run_repeating(callback_minute, interval=60, first=0)
    job_minute = j.run_repeating(callback_minute, interval = timedelta(hours = 1), first=0)


#    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    # Start the Bot
    updater.start_polling()
    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()

main()