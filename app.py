from flask import Flask, jsonify, request
import config
import database
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
    data = request.json

    good_data = data.get("good")
    if not good_data:
        return jsonify({"error"}), 400

    additions_data = data.get("additions", [])

    with session() as open_session:
        new_good = models.sql.Goods(
            goods_id=good_data["goods_id"],
            title=good_data["title"],
            description=good_data["description"],
            grams=good_data["grams"],
            photo_url=good_data["photo_url"],
            price=good_data["price"]
        )
        open_session.add(new_good)
        open_session.commit()

        for addition_data in additions_data:
            new_addition = models.sql.Additions(
                goods_id=new_good.goods_id,
                additions_id=addition_data["additions_id"],
                title=addition_data["title"],
                price=addition_data["price"]
            )
            open_session.add(new_addition)

        open_session.commit()

    return jsonify({"message": "success"}), 201


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