# AI Fitness Assistant

Проект с двумя версиями фитнес-ассистента:

- `v1` — старая рабочая версия с функциями `log_exercise`, `log_weight`, `get_exercise_history`, `get_weight_history`, `calculate_calories`.
- `v2` — новая версия в стиле урока: `Exercise`, `ListExercises`, `Agent` и работа через инструменты OpenAI.

## Установка

```bash
cd /Users/lyuba/Project/ai_fitness_assistant
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Конфигурация

Создайте файл `.env` в корне проекта:

```env
YANDEX_API_KEY=your_api_key
FOLDER_ID=your_folder_id
```

## Запуск

### Старый вариант (`v1`)

```bash
python main.py --version v1
```

### Новый вариант (`v2`)

```bash
python main.py --version v2
```

### Прямой запуск v2

```bash
python fitness_service_v2.py
```

## Структура проекта

- `main.py` — точка входа с переключателем между версиями
- `fitness_service.py` — старая версия
- `fitness_service_v2.py` — новая версия с Agent и инструментами
- `tools.py` — описание функций для OpenAI
- `requirements.txt` — зависимости проекта
