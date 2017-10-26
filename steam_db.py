# Подключим необходимые компоненты
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean  # ForeignKey - отвечает за связь с другой таблицей
from sqlalchemy import UniqueConstraint

engine = create_engine('sqlite:///steam.sqlite')  # выбираем БД, с которой будем работать (в данном случае sqlite). файл с БД будет называться blog.sqlite

db_session = scoped_session(sessionmaker(bind=engine))  # соединение с БД (получение-отправка данных)

Base = declarative_base()  # связываем сессию с БД. Декларативная база, т.е. опишем структуру таблиц в питон коде
Base.query = db_session.query_property()  # привязываем к declarative_base возможность делать запросы к БД

class Games(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer,unique=True)
    game_name = Column(String)
    discount = Column(Float)

    def __init__(self, game_id=None, game_name = None, discount=None):
        self.game_id = game_id
        self.game_name = game_name
        self.discount = discount

    def __repr__(self):
        return '<Games {} {} {} >'.format(self.game_id, self.game_name, self.discount)

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
