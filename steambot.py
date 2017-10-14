
import requests # позволяет получать инфо от сервера
import json

def get_info(url):
    result = requests.get(url)
 #   print(result.json()) # FYI метод со скобками, аттрибут - внутри. Мы получим не строку, а DICT
    if result.status_code == 200: #нужно всегда проверять, что вернул сервер
        return result.json()
    else:
        print("Something went wrong")

if __name__ == "__main__":
    game_id = "271590"
    data = get_info("http://store.steampowered.com/api/appdetails?appids=%s&cc=ru" % (game_id))
    name = data[game_id]["data"]["name"]
    prices = data[game_id]["data"]["price_overview"]
    print(name)
    print("http://store.steampowered.com/app/%s" % (game_id))

    for key,values in prices.items():
        print(key,":",values)


'''
при вызове функции мы получили данные в формате json. это НЕ питоновский словарь, но питон может ее преобразовать
у request есть функция для такого преобразования json

("https://apidata.mos.ru/v1/datasets/2009/rows/?api_key=c6a37e0e2a6057df193aee1ade88e16f")
'''


'''
the URI format of each API request is: 
https://api.steampowered.com/<interface>/<method>/v<version>/

GetNewsForApp (v0002)

GetNewsForApp returns the latest of a game specified by its appID.

Example URL: http://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid=440&count=3&maxlength=300&format=json
Arguments

    appid
        AppID of the game you want the news of.
    count
        How many news enties you want to get returned.
    maxlength
        Maximum length of each news entry.
    format
        Output format. json (default), xml or vdf.
'''