import typing

import re
from sqlalchemy import select
import models
import datetime
import config
import os
from PIL import Image


def glob_re(pattern, strings):
    return list(filter(re.compile(pattern).match, strings))


def clear_cache_images(images: list):
    [os.remove(config.STATIC_IMAGE_PATH+filename) for filename in images]


async def get_event_photo(photo_id, bot) -> str:

    time_now = datetime.datetime.now()
    new_image_filename = \
        f"photo_{time_now.year}-{time_now.month}-{time_now.day}_{photo_id}.webp"

    time_3_days_ago = datetime.datetime.now() - datetime.timedelta(days=3)

    old_images_path = "photo_{}-{}-{}_.*.webp".format(
        time_3_days_ago.year, time_3_days_ago.month, time_3_days_ago.day)

    cache_image_path = "photo_(.*)_{}.webp".format(photo_id)
    old_cache_images = glob_re(old_images_path, os.listdir(config.STATIC_IMAGE_PATH))
    if old_cache_images:
        clear_cache_images(old_cache_images)

    if glob_re(cache_image_path, os.listdir(config.STATIC_IMAGE_PATH)):
        cache_image = glob_re(cache_image_path, os.listdir(config.STATIC_IMAGE_PATH))[0]
        photo = f"/api/{config.STATIC_IMAGE_PATH}{cache_image}"
    else:
        await bot.download(photo_id, f"./data/images/{photo_id}.jpg", )
        image = Image.open(f"./data/images/{photo_id}.jpg")
        image.save(config.STATIC_IMAGE_PATH + new_image_filename, 'webp', optimize=True, quality=10)
        photo = f"/api/{config.STATIC_IMAGE_PATH}{new_image_filename}"

    return photo


async def get_events_photos(session, bot) -> list:
    photos = []

    with session() as open_session:
        events_in_db = open_session.execute(select(models.sql.NotPublicEvent))
        events_in_db: typing.List[models.sql.NotPublicEvent] = events_in_db.scalars().all()

    for event in events_in_db:

        time_now = datetime.datetime.now()
        new_image_filename =\
            f"photo_{time_now.year}-{time_now.month}-{time_now.day}_{event.photo_id}.webp"

        time_3_days_ago = datetime.datetime.now() - datetime.timedelta(days=3)

        old_images_path = "photo_{}-{}-{}_.*.webp".format(
            time_3_days_ago.year, time_3_days_ago.month, time_3_days_ago.day)

        cache_image_path = "photo_(.*)_{}.webp".format(event.photo_id)
        old_cache_images = glob_re(old_images_path, os.listdir(config.STATIC_IMAGE_PATH))
        if old_cache_images:
            clear_cache_images(old_cache_images)

        if glob_re(cache_image_path, os.listdir(config.STATIC_IMAGE_PATH)):
            cache_image = glob_re(cache_image_path, os.listdir(config.STATIC_IMAGE_PATH))[0]
            photos.append(f"/api/{config.STATIC_IMAGE_PATH}{cache_image}")
        else:
            await bot.download(event.photo_id, f"./data/images/{event.photo_id}.jpg",)
            image = Image.open(f"./data/images/{event.photo_id}.jpg")
            image.save(config.STATIC_IMAGE_PATH+new_image_filename, 'webp', optimize=True, quality=10)
            photos.append(f"/api/{config.STATIC_IMAGE_PATH}{new_image_filename}")

    return photos
