from steambot import get_info  # нужна ли эта функция?
import requests
import json
from bs4 import BeautifulSoup
import re
from steam_db import db_session, Games, User, User_Game
from sqlalchemy import exc
from sqlalchemy.orm import relationship
import logging

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='steam_parser.log'
                    )


def get_html(url):
    try:
        result = requests.get(url)
        result.raise_for_status()
        return result.text
    except requests.exceptions.RequestException:
        print ("get_html Error")
        return False

def check_username(username):
    print(username)
    html = get_html("https://steamcommunity.com/id/%s/wishlist/" % (username))
    bs = BeautifulSoup(html, "html.parser")
    error = bs.find("div", class_="error_ctn")
    hidden_page = bs.find("body", class_="flat_page profile_page private_profile responsive_page")
    if error is None and hidden_page is None:
        print("Юзернейм правильный")
        return True      
    else:
        print("Пользователя {} не существует, либо страница скрыта".format(username))
        return False

def wl_sales(username):
    print("test sales function")
    sales_result = list()
    html = get_html("https://steamcommunity.com/id/%s/wishlist/" % (username))
    bs = BeautifulSoup(html, "html.parser")
    wish_games = bs.find_all("div", "wishlistRow")
    for game in wish_games:
        game_id = re.search(r'([0-9]+)', game['id']).group(0)
        data = get_info("http://store.steampowered.com/api/appdetails?appids=%s&cc=ru" % (game_id))
        game_name = data[game_id]["data"]["name"]
        try:
            prices = data[game_id]["data"]["price_overview"]
        except KeyError:
            continue
        print(game_name)
        if prices["discount_percent"] > 0:
            sales_result.extend([game_name])
            sales_result.append("http://store.steampowered.com/app/%s" % (game_id))
            sales_result.extend([
                "{} RUB, Скидка: {} %".format(prices["final"]/100, prices["discount_percent"]),
                "Старая цена: {} RUB\n".format(prices["initial"]/100)
                ])                         
        else:
            pass
    return sales_result 
        
def wishlist_notifications(username,command):
    if check_username(username) is False:  # useful only if "name = main"
        return

    # return variables for telegram
    wishlist_result = list()
    notifications_result = list()

    html = get_html("https://steamcommunity.com/id/%s/wishlist/" % (username))   

    db_user = User.query.filter(User.username == username).first()  # будет значение None, если таких данных нет
    # add new username to DB 
    if db_user is None:
        db_session.add(User(username))
        db_user = User.query.filter(User.username == username).first()  # <User naash71> - то, что получим

    user_db_id = db_user.id  # get database user id

    bs = BeautifulSoup(html, "html.parser")
    wish_games = bs.find_all("div", "wishlistRow")
    all_games = []

    # нашли ID игр из WISHLIST пользователя

    for game in wish_games:
        game_id = re.search(r'([0-9]+)', game['id']).group(0)
        all_games.append(int(game_id))

    # нашли цены по ID игры из WISHLIST

        data = get_info("http://store.steampowered.com/api/appdetails?appids=%s&cc=ru" % (game_id))
        game_name = data[game_id]["data"]["name"]
        try:  # в Steam бывают игры без цены. устраняем KeyError. В БД не попадет
            prices = data[game_id]["data"]["price_overview"]
        except KeyError:
            print(game_name)
            print("Цена для данного продукта отсутствует\n")
            wishlist_result.extend([game_name,"Цена для данного продукта отсутствует\n"])
            continue
        print(game_name)
        print("http://store.steampowered.com/app/%s" % (game_id))
        wishlist_result.extend([game_name])
        wishlist_result.append("http://store.steampowered.com/app/%s" % (game_id))

        if prices["discount_percent"] == 0:
            print(prices["initial"]/100,"RUB")
            wishlist_result.extend(["{} RUB\n".format(prices["initial"]/100)])
        else:
            print(prices["final"]/100,"RUB,","Скидка:",prices["discount_percent"],"%\nСтарая цена:", prices["initial"]/100,"RUB")
            wishlist_result.extend([
                "{} RUB, Скидка: {} %".format(prices["final"]/100, prices["discount_percent"]),
                "Старая цена: {} RUB\n".format(prices["initial"]/100)
                ]) 
        print("\n")

        db_game = Games.query.filter(Games.game_id == game_id).first()

        if db_game is None:
            db_session.add(Games(game_id, game_name, prices["discount_percent"]))  # new game added to database
            db_game = Games.query.filter(Games.game_id == game_id).first()

        elif prices["discount_percent"] > db_game.discount:  # notification about discount
            print(game_name)
            print("http://store.steampowered.com/app/%s" % (game_id))
            print(prices["final"]/100,"RUB,","Скидка:",prices["discount_percent"],"%\nСтарая цена:", prices["initial"]/100,"RUB")
            print("\n")
            print("new discount")
            notifications_result.extend([
                game_name,
                "http://store.steampowered.com/app/%s" % (game_id),
                "{} RUB, Скидка: {} %".format(prices["final"]/100, prices["discount_percent"]),
                "Старая цена: {} RUB\n".format(prices["initial"]/100)
                ])

            db_game.discount = prices["discount_percent"]  # update discounts
            db_session.commit()
        else:
            db_game.discount = prices["discount_percent"]  # update discounts
            db_session.commit()  # почему с коммитом ниже не исполняется код?

        game_db_id = db_game.id  # get database game id
        # new unique relationship user-game added. If entry already exist, raise exception:
        try:
            db_session.add(User_Game(game_db_id, user_db_id))
            db_session.flush()
        except exc.IntegrityError:
            db_session.rollback()

    # get list of user games from DB
    g = db_session.query(Games).filter(Games.user.any(User.username == username)).all()  # get db_usergames through filter by username
    db_usergames = []
    for row in g:
        db_usergames.append(row.game_id)

    #  check if user has deleted game from steam wishlist
    for value in db_usergames:
        if not db_usergames:
            print("db_usergames list is empty, pass")
        elif value not in all_games:
    # if game has been removed from wishlist, remove entry from db User_Game table:  
            db_game = Games.query.filter(Games.game_id == value).first()
            game_db_id = db_game.id
            row_to_delete = db_session.query(User_Game).filter(User_Game.game_id == game_db_id, User_Game.user_id == user_db_id).first()
            print(row_to_delete,"row to delete")
            db_session.delete(row_to_delete)
            print("game {} deleted".format(value))

    db_session.commit()

    if command == "wishlist":
        return wishlist_result
        print(wishlist_result)
    elif command == "add":
        print(notifications_result)
        return notifications_result
    elif command == "sales":
        return wl_sales(username)
        

if __name__ == "__main__":
    username = "naash71"  # будет вводиться пользователем в сообщении telegram
    command = "wishlist"  # команда из telegram
    wishlist_notifications(username,command)
#    check_username(username)

'''
PRICE HTML PARSER:
wish_games_price = bs.find_all("div", "gameListPriceData")
for price in wish_games_price:
    href = price.find("a")
    print(price.text, href.get("href"))

cron - планировщик задач (стартует скрипт по расписанию), либо запускаю скрипт в вечном цикле с функцией засыпания на 24 часа sys sleep
'''