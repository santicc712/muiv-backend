import hashlib
import os
import ssl
import aiohttp
import certifi
from flask import Flask, jsonify, request
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from werkzeug.utils import secure_filename
import config
import database
import models
import validator
from models.sql.Question import Questions
from datetime import datetime

engine = create_engine("sqlite:///muiv.db", echo=True)
SessionLocal = sessionmaker(bind=engine)

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
    print(data.model_dump_json())
    return data.model_dump_json()

# --- Эндпоинт для отправки вопроса ---
@app.post("/api/questions")
async def submit_question():
    data = request.json

    # Проверка обязательных полей
    required_fields = ["role", "fio", "topic", "phone", "message"]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"status": "error", "message": f"Поле '{field}' обязательно"}), 400

    # Если студент, то проверяем поле group
    if data.get("role") == "student" and not data.get("group"):
        return jsonify({"status": "error", "message": "Поле 'group' обязательно для студентов"}), 400

    try:
        # Создаём объект Question
        question = Questions(
            role=data["role"],
            fio=data["fio"],
            topic=data["topic"],
            group=data.get("group"),
            phone=data["phone"],
            message=data["message"],
            created_at=datetime.utcnow()
        )

        # Сохраняем в БД
        session.add(question)
        session.commit()

        return jsonify({
            "status": "success",
            "message": "Ваш вопрос отправлен. В скором времени с вами свяжутся."
        }), 200

    except Exception as e:
        session.rollback()
        return jsonify({"status": "error", "message": f"Ошибка сохранения: {str(e)}"}), 500


@app.get("/api/questions")
async def get_questions():
    try:
        questions = session.query(Questions).all()

        result = [
            {
                "id": q.id,
                "role": q.role,
                "fio": q.fio,
                "topic": q.topic,
                "group": q.group,
                "phone": q.phone,
                "message": q.message,
                "created_at": q.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            for q in questions
        ]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка получения данных: {str(e)}"}), 500


# --- Эндпоинт для FAQ ---
@app.get("/api/faq")
async def get_faq():
    faq = [
        {
            "id": 1,
            "title": "Аккредитация",
            "link": "https://site/faq/accreditation"
        },
        {
            "id": 2,
            "title": "Набор на обучение",
            "link": "https://site/faq/admission"
        },
        {
            "id": 3,
            "title": "Процедура поступления",
            "link": "https://site/faq/enrollment"
        },
        {
            "id": 4,
            "title": "Оплата обучения",
            "link": "https://site/faq/payment"
        }
    ]
    return jsonify(faq), 200


# --- (Опционально) список тем обращения ---
@app.get("/api/topics")
async def get_topics():
    topics = [
        {"id": 1, "name": "Общее"},
        {"id": 2, "name": "Учебный процесс"},
        {"id": 3, "name": "Документы"},
        {"id": 4, "name": "Оплата"},
    ]
    return jsonify(topics), 200


# --- (Опционально) список групп ---
@app.get("/api/groups")
async def get_groups():
    groups = [
        {"id": 1, "name": "БИ-101"},
        {"id": 2, "name": "БИ-102"},
        {"id": 3, "name": "ПМИ-201"},
    ]
    return jsonify(groups), 200

# --- Эндпоинт авторизации сотрудника ---
@app.post("/api/staff/login")
async def staff_login():
    data = request.json

    # Проверка обязательных полей
    required_fields = ["login", "password"]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"status": "error", "message": f"Поле '{field}' обязательно"}), 400

    try:
        # Простейшая проверка (для примера)
        if data["login"] == "staff" and data["password"] == "1234":
            return jsonify({"status": "success", "token": "staff-fake-token"}), 200
        else:
            return jsonify({"status": "error", "message": "Неверный логин или пароль"}), 401

    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка авторизации: {str(e)}"}), 500


# --- Эндпоинт для выхода из аккаунта ---
@app.post("/api/staff/logout")
async def staff_logout():
    try:
        # Тут можно добавить логику очистки сессии
        return jsonify({"status": "success", "message": "Вы успешно вышли из аккаунта"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка выхода: {str(e)}"}), 500


# --- Эндпоинт получения списка обращений (с поиском) ---
@app.get("/api/staff/requests")
async def get_requests():
    try:
        search = request.args.get("search")  # поиск по номеру обращения

        # Для примера — список статических обращений
        requests_list = [
            {"id": 2415, "theme": "Практика", "status": "new"},
            {"id": 1252, "theme": "Оплата", "status": "in_progress"},
        ]

        if search:
            requests_list = [r for r in requests_list if str(r["id"]) == search]

        return jsonify(requests_list), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка получения списка обращений: {str(e)}"}), 500


# --- Эндпоинт получения деталей обращения ---
@app.get("/api/staff/requests/<int:request_id>")
async def get_request_detail(request_id):
    try:
        # В реальности данные подтягиваются из БД
        request_data = {
            "id": request_id,
            "fio": "Иванов Иван Иванович",
            "role": "student",
            "group": "ИвСС20.19",
            "theme": "Практика",
            "message": "Возможно ли пройти практику в университете? Какие нужны документы?",
        }
        return jsonify(request_data), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка получения данных обращения: {str(e)}"}), 500


# --- Эндпоинт ответа на обращение ---
@app.post("/api/staff/requests/<int:request_id>/answer")
async def answer_request(request_id):
    data = request.json

    if "answer" not in data or not data["answer"]:
        return jsonify({"status": "error", "message": "Поле 'answer' обязательно"}), 400

    try:
        # В реальности сохраняем ответ в БД
        return jsonify({
            "status": "success",
            "message": f"Ответ на обращение №{request_id} сохранён",
            "answer": data["answer"]
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка сохранения ответа: {str(e)}"}), 500

# --- Эндпоинт авторизации администратора (через общую форму) ---
@app.post("/api/admin/login")
async def admin_login():
    data = request.json

    required_fields = ["login", "password"]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"status": "error", "message": f"Поле '{field}' обязательно"}), 400

    try:
        # Пример проверки
        if data["login"] == "admin" and data["password"] == "admin123":
            return jsonify({
                "status": "success",
                "token": "admin-fake-token",
                "role": "admin"
            }), 200
        else:
            return jsonify({"status": "error", "message": "Неверный логин или пароль"}), 401

    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка авторизации: {str(e)}"}), 500


# --- Эндпоинт выхода администратора ---
@app.post("/api/admin/logout")
async def admin_logout():
    try:
        return jsonify({"status": "success", "message": "Вы вышли из аккаунта администратора"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка выхода: {str(e)}"}), 500


# --- Эндпоинт получения всех обращений (админ видит всё) ---
@app.get("/api/admin/requests")
async def admin_get_requests():
    try:
        requests_list = [
            {"id": 2415, "fio": "Иванов Иван", "theme": "Практика", "status": "new"},
            {"id": 1252, "fio": "Петров Петр", "theme": "Оплата", "status": "in_progress"},
        ]
        return jsonify(requests_list), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка получения обращений: {str(e)}"}), 500


# --- Эндпоинт просмотра деталей обращения ---
@app.get("/api/admin/requests/<int:request_id>")
async def admin_get_request_detail(request_id):
    try:
        request_data = {
            "id": request_id,
            "fio": "Иванов Иван Иванович",
            "role": "student",
            "group": "БИ-101",
            "theme": "Практика",
            "message": "Возможно ли пройти практику в университете?",
            "status": "new"
        }
        return jsonify(request_data), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка получения данных: {str(e)}"}), 500


# --- Эндпоинт удаления обращения ---
@app.delete("/api/admin/requests/<int:request_id>")
async def admin_delete_request(request_id):
    try:
        # Здесь удаляем запись из БД
        return jsonify({
            "status": "success",
            "message": f"Обращение №{request_id} удалено"
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка удаления: {str(e)}"}), 500


# --- Эндпоинт статистики обращений ---
@app.get("/api/admin/stats")
async def admin_get_stats():
    try:
        stats = {
            "total": 120,
            "new": 45,
            "in_progress": 30,
            "closed": 45
        }
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка получения статистики: {str(e)}"}), 500


if __name__ == "__main__":
    app.run("localhost", port=5001)
