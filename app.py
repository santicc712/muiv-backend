import asyncio
import logging
import os
import re
import typing
import requests
from validators import card

import config
from flask import Flask, jsonify, request, Response
from aiogram import Bot, types
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
import validator
import redis
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from datetime import datetime
import tools
import database
from sqlalchemy import select
import models
from redis.commands.json.path import Path
import aiofiles
from get_filepaths import get_filepaths_with_oswalk
import boto3

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


@app.post("/api/v1/user_info_tasks/<int:id>")
async def user_info_tasks(id: int):
    with session() as open_session:
        user = open_session.query(models.sql.User).filter(models.sql.User.id == id).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        telegram_channel_one = user.channel_one
        telegram_channel_two = user.channel_two
        instagram_channel = user.channel_inst

        referral_ids = open_session.query(models.sql.OwnerReferral.referral_user_id).filter(
            models.sql.OwnerReferral.owner_user_id == user.id).all()

        if not referral_ids:
            referral_list = []
        else:
            referrals = open_session.query(models.sql.User).filter(
                models.sql.User.id.in_([referral_id[0] for referral_id in referral_ids])).all()

            referral_list = [
                {
                    "id": referral.id,
                    "username": referral.username,
                    "money": referral.money,
                    "lvl": referral.lvl
                }
                for referral in referrals
            ]
        response_data = {
            "id": user.id,
            "referralLink": user.referral_link,
            "telegramChannelOne": telegram_channel_one,
            "telegramChannelTwo": telegram_channel_two,
            "instagramChannel": instagram_channel,
            "referrals": referral_list
        }

        return jsonify(response_data)


@app.get("/api/v1/info_users_top")
async def get_top_users():
    with session() as open_session:
        top_users = open_session.query(models.sql.User).order_by(models.sql.User.money.desc()).limit(10).all()

        user_list = [
            {
                "id": user.id,
                "username": user.username,
                "money": user.money,
                "lvl": user.lvl
            }
            for user in top_users
        ]

        return {"users": user_list}


@app.get("/api/v1/get_cards/<int:id>")
async def get_cards_info(id: int):
    with session() as open_session:
        all_cards = open_session.query(models.sql.Cards).all()

        purchased_ids_query = (
            open_session.query(models.sql.UserPurchased.card_id)
            .filter(models.sql.UserPurchased.id == id)
        )
        purchased_ids = set(card_id[0] for card_id in purchased_ids_query)

        cards_list = [
            {
                "card_id": card.card_id,
                "category": card.category,
                "photo_url": card.photo_url,
                "title": card.title,
                "profit": card.profit,
                "price": card.price,
                "purchased": card.card_id in purchased_ids
            }
            for card in all_cards
        ]

        return {"cards": cards_list}


if __name__ == "__main__":
    app.run("localhost", port=5001)
