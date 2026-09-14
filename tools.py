# Описание функций для Responses API

log_weight_tool = {
    "type": "function",
    "name": "log_weight",
    "description": "Записывает текущий вес пользователя",
    "parameters": {
        "type": "object",
        "properties": {
            "weight_kg": {
                "type": "number",
                "description": "Вес пользователя в килограммах",
            },
            "date": {
                "type": "string",
                "description": "Дата измерения в формате YYYY-MM-DD",
            },
            "user_id": {
                "type": "string",
                "description": "Идентификатор пользователя",
            },
        },
        "required": ["weight_kg"],
    },
}

get_weight_history_tool = {
    "type": "function",
    "name": "get_weight_history",
    "description": "Получает историю измерений веса пользователя",
    "parameters": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "Идентификатор пользователя",
            },
            "days": {
                "type": "integer",
                "description": "Количество дней для истории",
            },
        },
    },
}

calculate_calories_tool = {
    "type": "function",
    "name": "calculate_calories",
    "description": "Рассчитывает примерное количество сожжённых калорий",
    "parameters": {
        "type": "object",
        "properties": {
            "exercise_name": {
                "type": "string",
                "description": "Название упражнения",
            },
            "duration_minutes": {
                "type": "integer",
                "description": "Продолжительность в минутах",
            },
            "intensity": {
                "type": "string",
                "description": "Интенсивность тренировки",
            },
            "weight_kg": {
                "type": "number",
                "description": "Вес пользователя в кг",
            },
        },
        "required": ["exercise_name", "duration_minutes"],
    },
}

get_exercise_history_tool = {
    "type": "function",
    "name": "get_exercise_history",
    "description": "Получает историю тренировок пользователя за указанное количество дней",
    "parameters": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "Идентификатор пользователя",
            },
            "days": {
                "type": "integer",
                "description": "Количество дней для истории",
            },
        },
        "required": ["user_id"],
    },
}

log_exercise_tool = {
    "type": "function",
    "name": "log_exercise",
    "description": "Записывает информацию о выполненном упражнении в журнал тренировок",
    "parameters": {
        "type": "object",
        "properties": {
            "exercise_name": {
                "type": "string",
                "description": "Название упражнения",
            },
            "sets": {
                "type": "integer",
                "description": "Количество подходов",
            },
            "reps": {
                "type": "integer",
                "description": "Количество повторений в каждом подходе",
            },
            "weight": {
                "type": "number",
                "description": "Вес в кг (если применимо)",
            },
            "date": {
                "type": "string",
                "description": "Дата тренировки в формате YYYY-MM-DD (если не указана, используется сегодняшняя дата)",
            },
        },
        "required": ["exercise_name", "sets", "reps"],
    },
}

TOOLS = [
    log_exercise_tool,
    get_exercise_history_tool,
    calculate_calories_tool,
    log_weight_tool,
    get_weight_history_tool,
]

__all__ = [
    "log_exercise_tool",
    "get_exercise_history_tool",
    "calculate_calories_tool",
    "log_weight_tool",
    "get_weight_history_tool",
    "TOOLS",
]
