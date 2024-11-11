import os

from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename

import config
import database
import models

UPLOAD_FOLDER = 'static/uploads'
app = Flask(__name__, static_folder="static", static_url_path='/api/static/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif'}

db = database.implement.PostgreSQL(
    database_name=config.POSTGRESQL_DBNAME,
    username=config.POSTGRESQL_USER,
    password=config.POSTGRESQL_PASSWORD,
    hostname=config.POSTGRESQL_HOST,
    port=config.POSTGRESQL_PORT
)
session = database.manager.create_session(db)


@app.get("/api/v1/get_cards")
async def get_cards():
    with session() as open_session:
        goods = open_session.query(models.sql.Goods).all()
        goods_with_additions = []

        for good in goods:
            additions = open_session.query(models.sql.Additions).filter_by(goods_id=good.goods_id).all()
            good_data = {
                "goods_id": good.goods_id,
                "title": good.title,
                "description": good.description,
                "grams": good.grams,
                "photo_url": good.photo_url,
                "price": good.price,
                "additions": [
                    {
                        "additions_id": addition.additions_id,
                        "title": addition.title,
                        "price": addition.price
                    } for addition in additions
                ]
            }
            goods_with_additions.append(good_data)

        return jsonify(goods_with_additions)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/api/v1/add_card', methods=['POST'])
def add_card():
    # Получаем данные из формы
    good_goods_id = request.form.get('good[goods_id]')
    good_title = request.form.get('good[title]')
    good_description = request.form.get('good[description]')
    good_grams = request.form.get('good[grams]')
    good_price = request.form.get('good[price]')

    # Обработка файла (фото товара)
    photo_url = request.files.get('good[photo_url]')
    if photo_url and allowed_file(photo_url.filename):
        filename = secure_filename(photo_url.filename)
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo_url.save(photo_path)
    else:
        return jsonify({"error": "Invalid photo file"}), 400

    # Создание нового товара
    new_good = models.sql.Goods(
        goods_id=good_goods_id,
        title=good_title,
        description=good_description,
        grams=good_grams,
        price=good_price,
        photo_url=photo_path  # Ссылка на сохраненное фото
    )

    with session() as open_session:
        open_session.add(new_good)  # Добавляем товар в сессию
        open_session.commit()  # Сохраняем изменения в базе

        # Обработка дополнений
        additions = request.form.getlist('additions[0][additions_id]')
        additions_data = []
        for index in range(len(additions)):
            addition = models.sql.Additions(
                goods_id=good_goods_id,
                additions_id=additions[index],
                title=request.form.get(f'additions[{index}][title]'),
                price=request.form.get(f'additions[{index}][price]')
            )
            additions_data.append(addition)
            open_session.add(addition)  # Добавляем дополнение в сессию

        open_session.commit()  # Сохраняем изменения для дополнений

    # Отправляем успешный ответ
    return jsonify({
        "message": "Товар успешно добавлен!",
        "good_data": {
            "goods_id": good_goods_id,
            "title": good_title,
            "description": good_description,
            "grams": good_grams,
            "price": good_price,
            "photo_url": photo_path  # Ссылка на сохраненный файл
        },
        "additions": additions_data
    }), 201

@app.delete("/api/v1/delete_card/<int:card_id>")
async def delete_card(card_id):
    with session() as open_session:
        card = open_session.query(models.sql.Goods).filter_by(goods_id=card_id).first()

        if not card:
            return jsonify({"error": "no card"}), 404

        open_session.query(models.sql.Additions).filter_by(goods_id=card_id).delete()

        open_session.delete(card)
        open_session.commit()

    return jsonify({"message": "card delete"}), 200


if __name__ == "__main__":
    app.run("localhost", port=5001)