# Подключим необходимые компоненты
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean  # ForeignKey - отвечает за связь с другой таблицей
from sqlalchemy.orm import relationship
from sqlalchemy import UniqueConstraint

engine = create_engine('sqlite:///steam.sqlite')  # выбираем БД, с которой будем работать (в данном случае sqlite). файл с БД будет называться blog.sqlite

db_session = scoped_session(sessionmaker(bind=engine))  # соединение с БД (получение-отправка данных)

Base = declarative_base()  # связываем сессию с БД. Декларативная база, т.е. опишем структуру таблиц в питон коде
Base.query = db_session.query_property()  # привязываем к declarative_base возможность делать запросы к БД


# Добавим описание таблицы:
class User(Base):  # i.e. class users derives from class base all capabilities
    __tablename__ = 'users'  # name of DB - "users"
    id = Column(Integer, primary_key=True)  # creating of columns for DB table. primary_key=True - it mrans ID will be primary key
    username = Column(String, unique=True)# 100 length of string (customized value)
    user_games = relationship("Games",secondary = "user_game")

    def __init__(self, username=None):  # эти переменные будем присваивать атрибутам класса (выше)
        self.username = username # это обращения к своему собственному атрибуту

    def __repr__(self):  # то, что выведется на print
        return '<User {}>'.format(self.username)

class Games(Base): # создаем новый класс и таблицу
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer,unique=True)
    game_name = Column(String)
    discount = Column(Float)
    user = relationship("User", secondary = "user_game")

    def __init__(self, game_id=None, game_name = None, discount=None):
        self.game_id = game_id
        self.game_name = game_name
        self.discount = discount

    def __repr__(self):
        return '<Games {} {} {} >'.format(self.game_id, self.game_name, self.discount)

class User_Game(Base): # создаем таблицу связей
    __tablename__ = 'user_game'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer,ForeignKey('games.id'))
    user_id = Column(Integer,ForeignKey('users.id'))
    __table_args__ = (UniqueConstraint('game_id','user_id', name='game_user_unique_pair'),
                     )

    def __init__(self, game_id=None, user_id=None):
        self.game_id = game_id
        self.user_id = user_id

    def __repr__(self):
        return '<User_Game {} {} >'.format(self.game_id,self.user_id)

class Chat(Base):
    __tablename__ = 'chat'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, unique=True)
    tel_first_name = Column(String)
    tel_last_name = Column(String)
    notifications = Column(Boolean, default = False)
    username = Column(Integer)

    def __init__(self, chat_id=None, tel_first_name = None, tel_last_name = None, notifications=None, username = None):
        self.chat_id = chat_id
        self.tel_first_name = tel_first_name
        self.tel_last_name = tel_last_name
        self.notifications = notifications
        self.username = username

    def __repr__(self):
        return '<Chat {} {} {} {} {}>'.format(self.chat_id,self.tel_first_name,self.tel_last_name,self.notifications,self.username)


# Создадим нашу базу данных:
if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
