from databases import DatabaseURL
from starlette.config import Config
from starlette.datastructures import Secret


config = Config(".env")
PROJECT_NAME = "kaypoh"
VERSION = "1.0.0"
API_PREFIX = "/api"

SQLALCHEMY_DATABASE_URI = config("SQLALCHEMY_DATABASE_URI", cast=str)
