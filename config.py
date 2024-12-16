import os
from environs import Env

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

TERMINAL_KEY = env.str("TERMINAL_KEY")
PASSWORD = env.str("PASSWORD")

APP_URL = env.str("APP_URL")
