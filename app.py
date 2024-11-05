import config
from flask import Flask, jsonify, request, abort
from flask_socketio import SocketIO, emit
from aiogram import Bot, types
import validator
import database
import models

app = Flask(__name__, static_folder="static", static_url_path='/api/static/')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

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

        # Get user details
        response_data = {
            "id": user.id,
            "referralLink": user.referral_link,
            "money": user.money,
            "lvl": user.lvl,
            "profit": user.profit  # Assuming 'profit' is an attribute of User
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

@app.route("/api/v1/buy_card/<int:user_id>/<int:card_id>", methods=["POST"])
async def get_buy_card(user_id: int, card_id: int):
    with session() as open_session:
        card = open_session.query(models.sql.Cards).filter(models.sql.Cards.card_id == card_id).first()
        if not card:
            abort(404, description="Card not found")

        existing_purchase = open_session.query(models.sql.UserPurchased).filter(
            models.sql.UserPurchased.id == user_id,
            models.sql.UserPurchased.card_id == card_id
        ).first()

        if existing_purchase:
            abort(400, description="Card already purchased")

        new_purchase = models.sql.UserPurchased(id=user_id, card_id=card_id)
        open_session.add(new_purchase)
        open_session.commit()

        return {"status": "success", "message": "Card purchased successfully"}

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('request_update')
def handle_request_update(user_id):
    with session() as open_session:
        user = open_session.query(models.sql.User).filter(models.sql.User.id == user_id).first()
        if user:
            emit('update_user_info', {
                'id': user.id,
                'money': user.money,
                'lvl': user.lvl,
                'profit': user.profit
            })

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == "__main__":
    socketio.run(app, host="localhost", port=5001, allow_unsafe_werkzeug=True)
