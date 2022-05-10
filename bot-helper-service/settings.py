import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    USE_AWS_RDS: str = os.getenv("USE_AWS_RDS", "")
    USE_LOCAL_MYSQL: str = os.getenv("USE_LOCAL_MYSQL", "")

    AWS_RDS_CHANNEL_DATABASE_USER: str = os.getenv(
        "AWS_RDS_CHANNEL_DATABASE_USER", "user"
    )
    AWS_RDS_CHANNEL_DATABASE_PWD: str = os.getenv(
        "AWS_RDS_CHANNEL_DATABASE_PWD", "password"
    )
    AWS_RDS_URL: str = os.getenv("AWS_RDS_URL", "mysql:3306/db")
    AWS_RDS_SSL_CERT_PATH: str = os.getenv(
        "AWS_RDS_SSL_CERT_PATH", "/certs/rds-ca-2019-root.pem"
    )
    
    DB_USER: str = os.getenv("DB_USER", "user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    DB_HOST: str = os.getenv("DB_HOST", "mysql:3306")
    DB_NAME: str = os.getenv("DB_NAME", "db")
    
    SQLALCHEMY_DATABASE_SQL_LITE_URI = "sqlite:///:memory:"

    class Config:
        case_sensitive = True


settings = Settings()