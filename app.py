import hashlib
import os
import ssl
import aiohttp
import certifi
from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename
import config
import database
import models
import validator

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


@app.post("/api/checkInitData")
async def check_init_data():
    data = request.json
    data = validator.safe_parse_webapp_init_data(config.BOT_TOKEN, data["_auth"])

    return data.model_dump_json()


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
    good_goods_id = request.form.get('good[goods_id]')
    good_title = request.form.get('good[title]')
    good_description = request.form.get('good[description]')
    good_grams = request.form.get('good[grams]')
    good_price = request.form.get('good[price]')

    photo_url = request.files.get('good[photo_url]')
    if photo_url and allowed_file(photo_url.filename):
        filename = secure_filename(photo_url.filename)
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo_url.save(photo_path)
    else:
        return jsonify({"error": "Invalid photo file"}), 400

    new_good = models.sql.Goods(
        goods_id=good_goods_id,
        title=good_title,
        description=good_description,
        grams=good_grams,
        price=good_price,
        photo_url=photo_path
    )

    with session() as open_session:
        open_session.add(new_good)
        open_session.commit()

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
            open_session.add(addition)

        open_session.commit()

    return jsonify({
        "message": "Товар успешно добавлен!",
        "good_data": {
            "goods_id": good_goods_id,
            "title": good_title,
            "description": good_description,
            "grams": good_grams,
            "price": good_price,
            "photo_url": photo_path
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


def generate_tinkoff_token(terminal_key, amount=None, order_id=None, description=None, payment_id=None, password=None):
    params = {
        "TerminalKey": terminal_key,
        "Password": password
    }
    if amount is not None:
        params["Amount"] = str(amount)
    if order_id is not None:
        params["OrderId"] = order_id
    if description is not None:
        params["Description"] = description
    if payment_id is not None:
        params["PaymentId"] = payment_id

    concatenated_values = ''.join(params[key] for key in sorted(params.keys()))
    token = hashlib.sha256(concatenated_values.encode('utf-8')).hexdigest()
    return token


@app.post("/api/v1/init_payment")
async def init_payment():
    data = request.json
    user_id = data.get("user_id")
    goods_id = data.get("goods_id")
    price = data.get("price")

    with session() as open_session:
        goods = open_session.query(models.sql.Goods).filter_by(id=goods_id).first()
        if not goods:
            return jsonify({"error": "Товар не найден"}), 404

        terminal_key = config.TERMINAL_KEY
        password = config.PASSWORD
        order_id = f"{goods_id}_{user_id}"
        amount = int(goods_id.price * 100)
        description = f"Payment for quest {goods_id}"

        token = generate_tinkoff_token(terminal_key, amount, order_id, description, password=password)

        receipt = {
            "Email": "user@example.com",
            "Phone": "+71234567890",
            "Taxation": "osn",
            "Items": [
                {
                    "Name": f"Подарок {goods_id}",
                    "Price": amount,
                    "Quantity": 1.00,
                    "Amount": amount,
                    "Tax": "none",
                }
            ]
        }

        params = {
            "TerminalKey": terminal_key,
            "Amount": amount,
            "OrderId": order_id,
            "Description": description,
            "Token": token,
            "Receipt": receipt,
            "DATA": {
                "Phone": "+71234567890",
                "Email": "user@example.com"
            }
        }

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
            async with session.post("https://securepay.tinkoff.ru/v2/Init", json=params) as response:
                payment_data = await response.json()

                if payment_data.get("Success"):
                    payment_id = payment_data.get("PaymentId")
                    payment_url = payment_data.get("PaymentURL")
                    return jsonify({
                        "payment_url": payment_url,
                        "payment_id": payment_id,
                        "message": "Payment initialized successfully."
                    })
                else:
                    return jsonify({
                        "error": "Error initializing payment",
                        "message": payment_data.get("Message", "Unknown error")
                    }), 500


@app.post("/api/v1/confirm_payment")
async def confirm_payment():
    data = request.json
    payment_id = data.get("payment_id")
    order_id = data.get("order_id")

    terminal_key = config.TERMINAL_KEY
    password = config.PASSWORD
    token = generate_tinkoff_token(terminal_key, payment_id=payment_id, password=password)

    params = {
        "TerminalKey": terminal_key,
        "PaymentId": payment_id,
        "Token": token
    }

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        async with session.post("https://securepay.tinkoff.ru/v2/GetState", json=params) as response:
            payment_data = await response.json()

            if payment_data.get("Success") and payment_data.get("Status") == "CONFIRMED":
                quest_id = order_id.split('_')[0]
                user_id = order_id.split('_')[1]

                return jsonify({"message": "Payment confirmed and quest booked successfully."})
            else:
                return jsonify({"error": "Payment not confirmed."}), 400


if __name__ == "__main__":
    app.run("localhost", port=5001)
