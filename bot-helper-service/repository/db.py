from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from settings import settings


_USE_AWS_RDS = settings.USE_AWS_RDS
_AWS_RDS_URL = settings.AWS_RDS_URL
_AWS_RDS_CHANNEL_DATABASE_USER = settings.AWS_RDS_CHANNEL_DATABASE_USER
_AWS_RDS_CHANNEL_DATABASE_PWD = settings.AWS_RDS_CHANNEL_DATABASE_PWD
_AWS_RDS_SSL_CERT_PATH = settings.AWS_RDS_SSL_CERT_PATH

_USE_LOCAL_MYSQL = settings.USE_LOCAL_MYSQL
_DB_USER = settings.DB_USER
_DB_PASSWORD = settings.DB_PASSWORD
_DB_HOST = settings.DB_HOST
_DB_NAME = settings.DB_NAME

_SQLALCHEMY_DATABASE_SQL_LITE_URI = settings.SQLALCHEMY_DATABASE_SQL_LITE_URI


if _USE_AWS_RDS:
    SQLALCHEMY_DATABASE_URI = "mysql://{}:{}@{}?ssl_ca={}".format(
        _AWS_RDS_CHANNEL_DATABASE_USER,
        _AWS_RDS_CHANNEL_DATABASE_PWD,
        _AWS_RDS_URL,
        _AWS_RDS_SSL_CERT_PATH,
    )
    engine = create_engine(
        SQLALCHEMY_DATABASE_URI,
        convert_unicode=True,
        pool_size=5,
        max_overflow=10,
    )
elif _USE_LOCAL_MYSQL:
    SQLALCHEMY_DATABASE_URI = "mysql://{}:{}@{}/{}".format(
        _DB_USER,
        _DB_PASSWORD,
        _DB_HOST,
        _DB_NAME,
    )
    engine = create_engine(
        SQLALCHEMY_DATABASE_URI,
        convert_unicode=True,
        pool_size=5,
        max_overflow=10,
    )
else:
    print("USING LOCAL SQLite for testing")
    SQLALCHEMY_DATABASE_URI = _SQLALCHEMY_DATABASE_SQL_LITE_URI
    engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    import models
    Base.metadata.create_all(bind=engine, checkfirst=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
