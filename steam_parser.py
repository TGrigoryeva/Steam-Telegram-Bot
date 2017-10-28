import requests
from steambot import get_info
from bs4 import BeautifulSoup
import re
from steam_db import db_session, Games
from datetime import datetime, timedelta
import logging

# config
personal_wishlist_url = "https://steamcommunity.com/id/{}/wishlist/"
game_store_url = "http://store.steampowered.com/app/{}"
currency = "ru"
api_game_details_url = "http://store.steampowered.com/api/appdetails?appids={}&cc={}"

def get_html(url):
    try:
        result = requests.get(url)
        result.raise_for_status()
        return result.text
    except requests.exceptions.RequestException:
        print ("get_html Error")
        return False

def html_parser(username):
    html = get_html(personal_wishlist_url.format(username))
    bs = BeautifulSoup(html, "html.parser")
    return bs

def check_username(username):
    """  check if Steam id personal reference exists """
    try:
        error = html_parser(username).find("div", class_="error_ctn")
        hidden_page = html_parser(username).find("body", class_="flat_page profile_page private_profile responsive_page")
    except:
        print("Invalid URL")
        return False

    if not error and not hidden_page:
        print("Юзернейм {} правильный".format(username))
        return True      
    else:
        print("Пользователя {} не существует, либо страница скрыта".format(username))
        return False

def wl_sales(username):
    """ get list of games with discounts from user's wishlist"""
    sales_result = list()

    wish_games = html_parser(username).find_all("div", "wishlistRow")

    for game in wish_games:
        game_id = re.search(r'([0-9]+)', game['id']).group(0)
        data = get_info(api_game_details_url.format(game_id,currency))
        game_name = data[game_id]["data"]["name"]

        try:
            prices = data[game_id]["data"]["price_overview"]
        except KeyError:
            continue

        # print(game_name)

        if prices["discount_percent"] > 0:
            sales_result.extend([game_name])
            sales_result.append(game_store_url.format(game_id))
            sales_result.extend([
                "{} RUB, Скидка: {} %".format(prices["final"]/100, prices["discount_percent"]),
                "Старая цена: {} RUB\n".format(prices["initial"]/100)
                ])                         
        else:
            pass

    return sales_result 
        
def wishlist_notifications(username,command):

    # return variables for telegram
    wishlist_result = list()
    notifications_result = list()

    wish_games = html_parser(username).find_all("div", "wishlistRow")

    # нашли ID игр из WISHLIST пользователя
    for game in wish_games:
        game_id = re.search(r'([0-9]+)', game['id']).group(0)

        # нашли цены по ID игры из WISHLIST
        data = get_info(api_game_details_url.format(game_id,currency))
        game_name = data[game_id]["data"]["name"]

        # в Steam бывают игры без цены. устраняем KeyError. В БД не попадет
        try:  
            prices = data[game_id]["data"]["price_overview"]
        except KeyError:
            wishlist_result.extend([game_name,"Цена для данного продукта отсутствует\n"])
            continue

        wishlist_result.extend([game_name])
        wishlist_result.append(game_store_url.format(game_id))

        if prices["discount_percent"] == 0:
            wishlist_result.extend(["{} RUB\n".format(prices["initial"]/100)])
        else:
            wishlist_result.extend([
                "{} RUB, Скидка: {} %".format(prices["final"]/100, prices["discount_percent"]),
                "Старая цена: {} RUB\n".format(prices["initial"]/100)
                ]) 

        db_game = Games.query.filter(Games.game_id == game_id).first()

        if not db_game:
            db_session.add(Games(game_id, game_name, prices["discount_percent"]))  # new game added to database
            db_game = Games.query.filter(Games.game_id == game_id).first()

        if prices["discount_percent"] > db_game.discount:  # notification about discount

            notifications_result.extend([
                game_name,
                game_store_url.format(game_id),
                "{} RUB, Скидка: {} %".format(prices["final"]/100, prices["discount_percent"]),
                "Старая цена: {} RUB\n".format(prices["initial"]/100)
                ])

            # print(notifications_result)
        # print(wishlist_result)

    db_session.commit()

    if command == "wishlist":
        return wishlist_result
    elif command == "add":
        return notifications_result
    elif command == "sales":
        return wl_sales(username)

def db_discounts_update():
    """ Updates discounts values in database
        If new discount appears, fix the time for no futher actions within 6 hours,
        because while Steam sets new discount, discount values can change
        for many hours from the start.
        After 6 hours expired, delete time stamp
    """
    delta_hours = timedelta(hours = 6)
    current_time = datetime.now()
    timestamp_finish = current_time - delta_hours

    db_games = Games.query.all()

    for game in db_games:
        game_data = get_info(api_game_details_url.format(game.game_id,currency))

        try:
            prices = game_data[str(game.game_id)]["data"]["price_overview"]

            try:
                # update discounts values if timedelta for existing timestamp expired
                if not game.discount_start_time or timestamp_finish > game.discount_start_time:
                    
                    # if new discount appears, set timestamp in database
                    if prices["discount_percent"] > (game.discount):  
                        game.discount_start_time = datetime.now()
                        print("update: new discount {}".format(game.game_name))                        
                    else:
                        game.discount_start_time = None
                        print("update: price update {}".format(game.game_name))

                    game.discount = prices["discount_percent"]
            except:
                print("update: except {}".format(game.game_name)) 
                continue

        except:
            print("exception")
            continue

    db_session.commit()

if __name__ == "__main__":
    username = "naash71"  # будет вводиться пользователем в сообщении telegram
    command = "wishlist"  # команда из telegram
    wishlist_notifications(username,command)
#    db_discounts_update()
#    check_username(username)

'''
PRICE HTML PARSER:
wish_games_price = bs.find_all("div", "gameListPriceData")
for price in wish_games_price:
    href = price.find("a")
    print(price.text, href.get("href"))

cron - планировщик задач (стартует скрипт по расписанию), либо запускаю скрипт в вечном цикле с функцией засыпания на 24 часа sys sleep
'''