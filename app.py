import json
import os
from flask import Flask, jsonify, request
import config
import database
import models
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
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


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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


@app.post("/api/v1/add_card")
async def add_card():
    good_data = request.form.get("good")
    file = request.files.get("file")

    if not file or not good_data:
        return jsonify({"error": "error"}), 400

    good_data = json.loads(good_data)
    filename = f"goods_{good_data['goods_id']}.jpg"
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    with session() as open_session:
        new_good = models.sql.Goods(
            goods_id=good_data["goods_id"],
            title=good_data["title"],
            description=good_data["description"],
            grams=good_data["grams"],
            photo_url=f"/static/uploads/{filename}",
            price=good_data["price"]
        )
        open_session.add(new_good)
        open_session.commit()

        additions_data = json.loads(request.form.get("additions", "[]"))
        for addition_data in additions_data:
            new_addition = models.sql.Additions(
                goods_id=new_good.goods_id,
                additions_id=addition_data["additions_id"],
                title=addition_data["title"],
                price=addition_data["price"]
            )
            open_session.add(new_addition)
        open_session.commit()

    return jsonify({"message": "Card added successfully"}), 201


@app.delete("/api/v1/delete_card/<int:card_id>")
async def delete_card(card_id):
    with session() as open_session:
        card = open_session.query(models.sql.Goods).filter_by(goods_id=card_id).first()

        if not card:
            return jsonify({"error": "no card found"}), 404

        open_session.query(models.sql.Additions).filter_by(goods_id=card_id).delete()

        if card.photo_url:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], card.photo_url.split('/')[-1]))

        open_session.delete(card)
        open_session.commit()

    return jsonify({"message": "card deleted"}), 200


if __name__ == "__main__":
    app.run("localhost", port=5001)