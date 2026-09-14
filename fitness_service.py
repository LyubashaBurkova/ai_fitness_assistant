from __future__ import annotations
import uuid
from datetime import datetime, timedelta
from openai import OpenAI

from tools import (
    TOOLS,
    calculate_calories_tool,
    get_exercise_history_tool,
    get_weight_history_tool,
    log_exercise_tool,
    log_weight_tool,
)

import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("YANDEX_API_KEY") or os.getenv("api_key")
folder_id = os.getenv("FOLDER_ID") or os.getenv("folder_id")


client = OpenAI(
    base_url="https://ai.api.cloud.yandex.net/v1",
    api_key=api_key,
    project=folder_id,
)

model = f"gpt://{folder_id}/qwen3-235b-a22b-fp8/latest"

exercises_db = {
    "users": {},
    "exercise_log": [],
    "weight_log": [],
}


def log_exercise(
    exercise_name,
    sets,
    reps,
    weight=None,
    date=None,
    user_id="default",
):
    """Записывает информацию о выполненном упражнении в журнал тренировок."""
    record_id = str(uuid.uuid4())

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    record = {
        "id": record_id,
        "user_id": user_id,
        "exercise": exercise_name,
        "sets": sets,
        "reps": reps,
        "weight": weight,
        "date": date,
    }

    if "exercise_log" not in exercises_db:
        exercises_db["exercise_log"] = []

    exercises_db["exercise_log"].append(record)

    return {
        "status": "success",
        "message": f"Упражнение '{exercise_name}' успешно записано",
        "record_id": record_id,
    }


def log_weight(weight_kg, date=None, user_id="default"):
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    record_id = str(uuid.uuid4())

    record = {
        "id": record_id,
        "user_id": user_id,
        "weight_kg": weight_kg,
        "date": date,
    }

    exercises_db["weight_log"].append(record)

    return {
        "status": "success",
        "message": f"Вес {weight_kg} кг успешно записан",
        "record_id": record_id,
    }


def get_weight_history(user_id="default", days=30):
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    history = [
        record
        for record in exercises_db["weight_log"]
        if record.get("user_id") == user_id and record.get("date") >= start_date
    ]

    return {
        "status": "success",
        "history": history,
    }


def get_exercise_history(user_id="default", days=7):
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    history = [
        record
        for record in exercises_db["exercise_log"]
        if record.get("user_id") == user_id and record.get("date") >= start_date
    ]

    return {
        "status": "success",
        "history": history,
    }


def calculate_calories(exercise_name, duration_minutes, intensity="moderate", weight_kg=70):
    met_values = {
        "бег": {"low": 7, "moderate": 9, "high": 12},
        "ходьба": {"low": 3, "moderate": 4, "high": 5},
        "плавание": {"low": 5, "moderate": 7, "high": 10},
        "велосипед": {"low": 4, "moderate": 6, "high": 8},
        "приседания": {"low": 3, "moderate": 5, "high": 7},
        "отжимания": {"low": 3, "moderate": 5, "high": 8},
        "default": {"low": 3, "moderate": 5, "high": 7},
    }

    exercise_name_lower = exercise_name.lower()
    exercise_met = met_values.get(exercise_name_lower, met_values["default"])
    met = exercise_met.get(intensity, exercise_met["moderate"])

    calories = met * weight_kg * (duration_minutes / 60)

    return {
        "status": "success",
        "exercise": exercise_name,
        "duration_minutes": duration_minutes,
        "intensity": intensity,
        "calories_burned": round(calories, 1),
        "met_used": met,
    }


def call_model(prompt: str, user_id: str = "default"):
    response = client.responses.create(
        model=model,
        instructions="Ты — профессиональный фитнес-ассистент. Помогаешь пользователю вести дневник тренировок.",
        input=prompt,
        tools=TOOLS,
    )
    return response


__all__ = [
    "log_exercise",
    "log_weight",
    "get_weight_history",
    "get_exercise_history",
    "calculate_calories",
    "call_model",
]
