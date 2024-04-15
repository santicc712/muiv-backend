import os
from environs import Env
import tools
import models


env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")

DIRNAME = os.path.dirname(__file__)
# os.chdir(f"{DIRNAME}//..")
STATIC_IMAGE_PATH = "static/images/"

POSTGRESQL_HOST = env.str("POSTGRESQL_HOST")
POSTGRESQL_PORT = env.str("POSTGRESQL_PORT")
POSTGRESQL_USER = env.str("POSTGRESQL_USER")
POSTGRESQL_PASSWORD = env.str("POSTGRESQL_PASSWORD")
POSTGRESQL_DBNAME = env.str("POSTGRESQL_DBNAME")

APP_URL = env.str("APP_URL")

REDIS_HOST = env.str("REDIS_HOST")
REDIS_PORT = env.int("REDIS_PORT")
REDIS_USERNAME = env.str("REDIS_USERNAME")
REDIS_PASSWORD = env.str("REDIS_PASSWORD")

