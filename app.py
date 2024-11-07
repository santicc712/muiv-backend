import config
from flask import Flask, jsonify, request, Response
from aiogram import Bot, types
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
import validator
import database
from sqlalchemy import select
import models

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app = Flask(__name__, static_folder="static", static_url_path='/api/static/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = database.implement.PostgreSQL(
    database_name=config.POSTGRESQL_DBNAME,
    username=config.POSTGRESQL_USER,
    password=config.POSTGRESQL_PASSWORD,
    hostname=config.POSTGRESQL_HOST,
    port=config.POSTGRESQL_PORT
)

session = database.manager.create_session(db)


@app.post("/api/checkInitData")
async def check_init_data():
    data = request.json
    data = validator.safe_parse_webapp_init_data(config.BOT_TOKEN, data["_auth"])

    return data.model_dump_json()


# @app.get("/api/v1/my_account/<int:user_id>")
# async def get_account_info(user_id):
#     with session() as open_session:
#         user = open_session.query(models.sql.User).filter(models.sql.User.id == id).first()
#         user_data = [
#             {
#                 "id": user.id,
#                 "username": user.username,
#                 "money": user.money,
#                 "lvl": user.lvl
#             }
#         ]
#         return user_data


if __name__ == "__main__":
    app.run("localhost", port=5001)

