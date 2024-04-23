import asyncio
import logging
import os
import re
import typing
import requests
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
bucket_name = 'a7f02a62-e15c7451-cea6-4e82-9754-31fa55629677'

data = dict(
    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
    endpoint_url=config.AWS_ENDPOINT_URL,
    region_name=config.AWS_DEFAULT_REGION
)

sqs = boto3.client('sqs', **data)
s3 = boto3.resource('s3', **data)

def upload_static_file(file_path, key):
    s3.Object(bucket_name, key).upload_file(file_path)


def get_static_file_url(key):
    return f"https://{bucket_name}.s3.timeweb.cloud/{key}"


async def get_user_photo_url(user_id: int):
    bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)

    photos = await bot.get_user_profile_photos(user_id, limit=1)

    try:
        current_photo = await bot.get_file(photos.photos[0][0].file_id)
        photo_url = bot.get_file_url(current_photo.file_path)
    except IndexError:
        photo_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSrYO97QZyLAUdjVTXl8n2tzoce2lBmZMBf1g&usqp=CAU"

    await bot.close()
    return photo_url


@app.post("/api/checkInitData")
async def check_init_data():
    data = request.json
    data = validator.safe_parse_webapp_init_data(config.BOT_TOKEN, data["_auth"])

    return data.model_dump_json()


@app.post("/api/createCampaign")
async def create_campaign():
    data = request.form

    with session() as open_session:
        campaign = open_session.execute(select(models.sql.Campaign).filter_by(id=data["id"]))
        campaign: models.sql.Campaign = campaign.scalars().first()

    if campaign:
        return jsonify(dict(status=400))

    if data["one_by_access"] == "true":
        one_by_access = True
    else:
        one_by_access = False

    finish_date = data["finish_date"]
    if not finish_date:
        finish_date = "active"

    with session() as open_session:
        new_campaign = models.sql.Campaign(
            id=data["id"],
            title=data["title"],
            desc=data["desc"],
            one_by_access=one_by_access,
            reward_currency=data["reward_currency"],
            reward_amount=data["reward_amount"],
            finish_date=finish_date,
            finish_time=data["finish_time"],
            created_at=datetime.now()
        )
        open_session.merge(new_campaign)
        open_session.commit()

    return jsonify(dict(status=200))


@app.post("/api/deleteCampaign")
async def delete_campaign():
    data = request.json
    status = None

    with session() as open_session:
        campaign = open_session.execute(select(models.sql.Campaign).filter_by(id=data["campaign_id"]))
        campaign: models.sql.Campaign = campaign.scalars().first()

        if campaign:
            open_session.delete(campaign)
            open_session.commit()
            status = 200

    return jsonify(dict(status=status))


@app.post("/api/editCampaign")
async def edit_campaign():
    data = request.form

    with session() as open_session:
        campaign = open_session.execute(select(models.sql.Campaign).filter_by(id=data["id"]))
        campaign: models.sql.Campaign = campaign.scalars().first()

        if campaign:
            open_session.delete(campaign)
            open_session.commit()

    if data["one_by_access"] == "true":
        one_by_access = True
    else:
        one_by_access = False

    with session() as open_session:
        new_campaign = models.sql.Campaign(
            id=data["id"],
            title=data["title"],
            desc=data["desc"],
            one_by_access=one_by_access,
            reward_currency=data["reward_currency"],
            reward_amount=data["reward_amount"],
            finish_date=data["finish_date"],
            finish_time=data["finish_time"],
            created_at=datetime.now()
        )
        open_session.merge(new_campaign)
        open_session.commit()

    return jsonify(dict(status=200))


@app.get("/api/getCampaigns")
async def get_campaigns():

    with session() as open_session:
        campaigns = open_session.execute(select(models.sql.Campaign))
        campaigns: typing.List[models.sql.Campaign] = campaigns.scalars().all()

    events = []
    for c in campaigns:
        time_unit = ""
        time_left_value = 0

        if str(c.finish_date) == "active":
            time_left_value = 999
        elif re.findall("\d{2}/\d{2}/\d{4}", str(c.finish_date)) and re.findall("\d{2}:\d{2}", str(c.finish_time)):
            finish_datetime_str = c.finish_date + " " + c.finish_time
            finish_datetime = datetime.strptime(finish_datetime_str, "%d/%m/%Y %H:%M")
            now_datetime = datetime.now()

            time_left = finish_datetime - now_datetime

            days_left = time_left.days
            hours_left = time_left.total_seconds() // 3600
            time_unit = "days"
            time_left_value = days_left

            if days_left < 1:
                time_unit = "hours"
                time_left_value = hours_left

            if hours_left < 1:
                time_left_value = 0

        campaign_image = f"{UPLOAD_FOLDER}/campaign_media_{c.id}.jpg"
        reward_image = f"{UPLOAD_FOLDER}/reward_media_{c.id}.jpg"
        events.append(
            dict(
                id=c.id,
                image=get_static_file_url(campaign_image),
                title=c.title,
                desc=c.desc,
                time_left=time_left_value,
                time_unit=time_unit,
                reward_currency=c.reward_currency,
                reward_amount=c.reward_amount,
                reward_image=get_static_file_url(reward_image),
            )
        )

    events.reverse()
    return jsonify(dict(events=events))


@app.post("/api/getCampaign")
async def get_campaign():
    data = request.json
    with session() as open_session:
        campaign = open_session.execute(select(models.sql.Campaign).filter_by(id=data["campaign_id"]))
        campaign: models.sql.Campaign = campaign.scalars().first()

    time_unit = ""
    time_left_value = 0

    if str(campaign.finish_date) == "active":
        time_left_value = 999

    elif re.findall("\d{2}/\d{2}/\d{4}", str(campaign.finish_date)) and re.findall("\d{2}:\d{2}", str(campaign.finish_time)):
        # "12/02/2024" + "10:00"
        finish_datetime_str = campaign.finish_date + " " + campaign.finish_time

        finish_datetime = datetime.strptime(finish_datetime_str, "%d/%m/%Y %H:%M")
        now_datetime = datetime.now()

        time_left = finish_datetime - now_datetime

        days_left = time_left.days
        hours_left = time_left.total_seconds() // 3600

        time_unit = "days"
        time_left_value = days_left

        if days_left < 1:
            time_unit = "hours"
            time_left_value = hours_left

        if hours_left < 1:
            time_left_value = 0

    campaign_image = f"{UPLOAD_FOLDER}/campaign_media_{campaign.id}.jpg"
    reward_image = f"{UPLOAD_FOLDER}/reward_media_{campaign.id}.jpg"
    campaign_dict = dict(
        id=data["campaign_id"],
        url=f"https://t.me/RaiseAnon_bot/campaign?startapp={data['campaign_id']}",
        title=campaign.title,
        desc=campaign.desc,
        one_by_access=campaign.one_by_access,
        time_left=time_left_value,
        time_unit=time_unit,
        image=get_static_file_url(campaign_image),
        reward_currency=campaign.reward_currency,
        reward_amount=campaign.reward_amount,
        reward_image=get_static_file_url(reward_image),

    )

    return jsonify(dict(campaign=campaign_dict))


def get_file_extension(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower()


@app.get("/api/getRandomHash")
async def get_random_hash():
    return jsonify(dict(data=tools.hash_generator.generate()))


@app.get("/api/getAdmins")
async def get_admins():
    with session() as open_session:
        admins = open_session.execute(select(models.sql.Admin))
        admins: typing.List[models.sql.Admin] = admins.scalars().all()
        admins: list[int] = [i.id for i in admins]

    return jsonify(dict(admins=admins))


@app.post("/api/addCampaignTaskGroups")
async def add_task():
    campaign_id: str = request.json["campaign_id"]
    task_groups: list = request.json["task_groups"]

    r = redis.StrictRedis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        username=config.REDIS_USERNAME,
        password=config.REDIS_PASSWORD,
        db=0,
        decode_responses=True
    )
    r.json().set(f"campaign_task_groups:{campaign_id}", Path.root_path(), task_groups)
    return jsonify(dict(status=200))


@app.post("/api/getCampaignTaskGroups")
async def get_task():
    campaign_id: str = request.json["campaign_id"]
    user_id: str = request.json["user_id"]
    one_by_one_access = request.json["one_by_access"]

    r = redis.StrictRedis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        username=config.REDIS_USERNAME,
        password=config.REDIS_PASSWORD,
        db=0,
        decode_responses=True
    )
    task_groups = r.json().get(f"campaign_task_groups:{campaign_id}")

    with session() as open_session:
        done_tasks = open_session.execute(
            select(models.sql.DoneTask).filter_by(campaign_id=campaign_id, user_id=user_id))
        done_tasks: typing.List[models.sql.DoneTask] = done_tasks.scalars().all()

    for done_task in done_tasks:
        group_id = done_task.group_id
        task_id = done_task.task_id
        for group in task_groups:
            if group["id"] == group_id:
                for task in group["tasks"]:
                    if task["id"] == task_id:
                        task["is_done"] = True

    if one_by_one_access:
        is_blocked = False
        for group in task_groups:
            for task in group["tasks"]:
                if task["is_done"]:
                    continue
                elif is_blocked:
                    task["is_blocked"] = True
                else:
                    is_blocked = True

    not_done_tasks = [
        dict(task=task, group_id=group["id"]) for group in task_groups for task in group["tasks"] if not task["is_done"]
    ]
    return jsonify(dict(task_groups=task_groups, not_done_tasks=not_done_tasks))


@app.post("/api/setDoneCampaign")
async def set_done_campaign():
    campaign_id: str = request.json["campaign_id"]
    user_id: int = request.json["user_id"]
    username: str = request.json["username"]
    return_status = 200

    with session() as open_session:
        done_campaign = open_session.execute(
            select(models.sql.DoneCampaign).filter_by(campaign_id=campaign_id, user_id=user_id))
        done_campaign: models.sql.DoneCampaign = done_campaign.scalars().first()

        if not done_campaign:
            new_done_campaign = models.sql.DoneCampaign(
                campaign_id=campaign_id,
                user_id=user_id,
                username=username
            )
            open_session.merge(new_done_campaign)
            open_session.commit()
        else:
            return_status = 400

    return jsonify(dict(status=return_status))


@app.post("/api/sendDoneCampaignUsers")
async def send_done_campaign_users():
    campaign_id: str = request.json["campaign_id"]
    user_id: int = request.json["user_id"]

    bot = Bot(token=config.BOT_TOKEN, parse_mode="html")

    with session() as open_session:
        done_campaign_users = open_session.execute(
            select(models.sql.DoneCampaign).filter_by(campaign_id=campaign_id))
        done_campaign_users: typing.List[models.sql.DoneCampaign] = done_campaign_users.scalars().all()

        user_wallets = open_session.execute(
            select(models.sql.UserWallet).filter_by(campaign_id=campaign_id))
        user_wallets: typing.List[models.sql.UserWallet] = user_wallets.scalars().all()

    file = f"users_{campaign_id}.txt"
    async with aiofiles.open(file, mode='w') as f:
        for user in done_campaign_users:
            user_wallet = [i.wallet for i in user_wallets if i.user_id == user.user_id]
            await f.write(f"{user.username}|{user.user_id}|{user_wallet}\n")

    await bot.send_document(
        chat_id=user_id,
        document=types.FSInputFile(file)
    )

    os.remove(file)
    await bot.close()
    return jsonify(dict(status=200))


@app.post("/api/getDoneCampaign")
async def get_done_campaign_stats():
    campaign_id: str = request.json["campaign_id"]

    bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)

    with session() as open_session:
        done_campaign_users = open_session.execute(
            select(models.sql.DoneCampaign).filter_by(campaign_id=campaign_id))
        done_campaign_users: typing.List[models.sql.DoneCampaign] = done_campaign_users.scalars().all()

    return jsonify(dict(campaign_count=len(done_campaign_users)))


@app.get("/api/getDoneCampaigns")
async def get_done_campaigns():
    with session() as open_session:
        done_campaigns = open_session.execute(
            select(models.sql.DoneCampaign.campaign_id))
        done_campaigns: typing.List[str] = done_campaigns.scalars().all()

    done_campaigns = set(done_campaigns)

    if not done_campaigns:
        return jsonify(dict(events=[]))
    else:
        events = []
        for c in done_campaigns:
            time_unit = ""
            time_left_value = 0

            with session() as open_session:
                done_campaign = open_session.execute(select(models.sql.Campaign).filter_by(id=c))
                done_campaign: models.sql.Campaign = done_campaign.scalars().first()

            if str(done_campaign.finish_date) == "active":
                time_left_value = 999
            elif (re.findall("\d{2}/\d{2}/\d{4}", str(done_campaign.finish_date))
                    and re.findall("\d{2}:\d{2}", str(done_campaign.finish_time))):
                finish_datetime_str = done_campaign.finish_date + " " + done_campaign.finish_time
                finish_datetime = datetime.strptime(finish_datetime_str, "%d/%m/%Y %H:%M")
                now_datetime = datetime.now()

                time_left = finish_datetime - now_datetime

                days_left = time_left.days
                hours_left = time_left.total_seconds() // 3600
                time_unit = "days"
                time_left_value = days_left

                if days_left < 1:
                    time_unit = "hours"
                    time_left_value = hours_left

                if hours_left < 1:
                    time_left_value = 0

            campaign_image = f"{UPLOAD_FOLDER}/campaign_media_{c}.jpg"
            reward_image = f"{UPLOAD_FOLDER}/reward_media_{c}.jpg"
            events.append(
                dict(
                    id=c,
                    image=get_static_file_url(campaign_image),
                    title=done_campaign.title,
                    desc=done_campaign.desc,
                    time_left=time_left_value,
                    time_unit=time_unit,
                    reward_currency=done_campaign.reward_currency,
                    reward_amount=done_campaign.reward_amount,
                    reward_image=get_static_file_url(reward_image),
                )
            )

        events.reverse()
        return jsonify(dict(events=events))


@app.post("/api/setDoneTask")
async def set_done_task():
    campaign_id: str = request.json["campaign_id"]
    user_id: str = request.json["user_id"]
    task_id: int = request.json["task_id"]
    group_id: int = request.json["group_id"]

    with session() as open_session:
        new_done_task = models.sql.DoneTask(
            campaign_id=campaign_id,
            user_id=user_id,
            task_id=task_id,
            group_id=group_id
        )
        open_session.merge(new_done_task)
        open_session.commit()

    return jsonify(dict(status=200))


@app.post("/api/uploadCampaignImage")
async def upload_campaign_image():
    data = request.form
    file = request.files['media']

    if not file:
        pass

    file_extension = get_file_extension(file.filename)
    if file_extension not in ALLOWED_EXTENSIONS:
        pass

    file.save(os.path.join(app.config['UPLOAD_FOLDER'], f"campaign_media_{data['id']}.jpg"))
    filepath = f"{UPLOAD_FOLDER}/campaign_media_{data['id']}.jpg"
    upload_static_file(filepath, filepath)

    return jsonify(dict(status=200))


@app.post("/api/uploadRewardImage")
async def upload_reward():
    data = request.form
    file = request.files['media']

    if not file:
        pass

    file_extension = get_file_extension(file.filename)
    if file_extension not in ALLOWED_EXTENSIONS:
        pass

    file.save(os.path.join(app.config['UPLOAD_FOLDER'], f"reward_media_{data['id']}.jpg"))
    filepath = f"{UPLOAD_FOLDER}/reward_media_{data['id']}.jpg"
    upload_static_file(filepath, filepath)

    return jsonify(dict(status=200))


@app.post("/api/uploadTaskStories")
async def uploadTaskStory():
    data = request.form

    for name in request.files:
        file = request.files[name]
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], f"story_{data['story_id']}_{name}.jpg"))
        filepath = f"{UPLOAD_FOLDER}/story_{data['story_id']}_{name}.jpg"
        upload_static_file(filepath, f"static/stories/{data['story_id']}/{name}.jpg")

    return jsonify(dict(status=200))


@app.post("/api/getStories")
async def get_stories():
    data = request.json
    folder_name = f"static/stories/{data['story_id']}"
    response = sqs.list_objects(Bucket=bucket_name, Prefix=folder_name)
    stories = [get_static_file_url(obj['Key']) for obj in response['Contents'] if obj['Key'].endswith('.jpg')]
    return jsonify(dict(stories=stories))


@app.post("/api/setUserWallet")
async def set_user_wallet():
    campaign_id: str = request.json["campaign_id"]
    user_id: int = request.json["user_id"]
    wallet: str = request.json["wallet"]

    with session() as open_session:
        user_wallet = open_session.execute(
            select(models.sql.UserWallet).filter_by(user_id=user_id, campaign_id=campaign_id))
        user_wallet = user_wallet.scalars().first()
        if not user_wallet:
            new_wallet = models.sql.UserWallet(
                campaign_id=campaign_id,
                user_id=user_id,
                wallet=wallet[:50]
            )
            open_session.merge(new_wallet)
        else:
            user_wallet.wallet = wallet[:50]

        open_session.commit()

    return jsonify(dict(status=200))

if __name__ == "__main__":
    app.run("localhost", port=5001)






