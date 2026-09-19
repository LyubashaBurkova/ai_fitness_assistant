from __future__ import annotations

import json
import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from weather import weather_tool

load_dotenv()

api_key = os.getenv("YANDEX_API_KEY") or os.getenv("api_key")
folder_id = os.getenv("FOLDER_ID") or os.getenv("folder_id")

client = OpenAI(
    base_url="https://ai.api.cloud.yandex.net/v1",
    api_key=api_key,
    project=folder_id,
)

model = f"gpt://{folder_id}/qwen3-235b-a22b-fp8/latest"

#try:
#    vector_store = client.vector_stores.create(name="rag_store")
#except Exception:
#    vector_store = None

#search_tool = None

#if vector_store is not None:
#    search_tool = {
#        "type": "file_search",
#        "vector_store_ids": [vector_store.id],
#        "max_num_results": 5,
#    }

vector_store_id = "fvt3dc3lfoni7tfbu7e5"

search_tool = {
    "type": "file_search",
    "vector_store_ids": [vector_store_id],
    "max_num_results": 5,
}

notes_tool = {
    "type": "mcp",
    "server_label": "PersonalNotes",
    "server_url": "http://89.169.168.105:8000/sse",
    "require_approval": "never",
}

exercise_db = {}


class Exercise(BaseModel):
    """Добавляет информацию о сделанном в зале упражнении."""

    тип: Optional[str] = Field(description="Тип упражнения (кардио или силовое)", default=None)
    название: Optional[str] = Field(description="Название упражнения", default=None)
    болевые_ощущения: Optional[str] = Field(description="Болевые ощущения при выполнении упражнения", default=None)
    пульс: Optional[int] = Field(description="Пульс в момент выполнения упражнения", default=None)
    подходы: Optional[int] = Field(description="Количество подходов", default=None)
    повторения: Optional[int] = Field(description="Количество повторений", default=None)

    # Связь с ListExercises:
    # - process() сохраняет экземпляр Exercise в exercise_db[session_id]
    # - ListExercises.process() читает эти данные и форматирует список
    """
    process создаёт запись в глобальном словаре exercise_db
    
    ListExercises.process(session_id):
        читает из того же exercise_db[session_id]
        проходит по списку и обращается к полям объекта:
        x.название
        x.тип
        x.подходы
        x.повторения

    Exercise отвечает за запись данных
    ListExercises отвечает за чтение тех же данных

    оба работают с одним и тем же глобальным словарём exercise_db
    оба ожидают, что там лежат объекты Exercise
    """
    def process(self, session_id):
        """Сохраняет упражнение в базе данных для конкретной сессии."""
        if session_id not in exercise_db:
            exercise_db[session_id] = []
        exercise_db[session_id].append(self)
        return "Упражнение добавлено"


class ListExercises(BaseModel):
    """Возвращает список сделанных упражнений для сессии."""

    def process(self, session_id):
        """Возвращает список упражнений для указанной сессии."""
        if session_id not in exercise_db:
            return "Упражнений нет"

        return "\n".join(
            [
                f"{i + 1}. {x.название} ({x.тип}, {x.подходы} подходов, {x.повторения} повторений)"
                for i, x in enumerate(exercise_db[session_id])
            ]
        )


def _create_tool_annot(x):
    """Преобразует Pydantic-модель в описание инструмента для OpenAI."""
    if isinstance(x, dict):
        return x

    if issubclass(x, BaseModel):
        # issubclass() проверяет, что x — класс, наследуемый от BaseModel.
        # Для такого класса создаётся tool schema для OpenAI Responses API.
        return {
            "type": "function",
            "name": x.__name__,
            "description": x.__doc__,
            "parameters": x.model_json_schema(),
        }

    return x


# Расширенный класс агента с поддержкой объектов-инструментов
"""Agent — это расширенный класс агента, который поддерживает работу с объектами-инструментами.
Он принимает инструкцию, список инструментов, модель и выбор инструмента.
Внутри класса создаётся отображение инструментов по имени и список инструментов с аннотациями.
Также реализован метод __call__, который обрабатывает сообщения пользователя, вызывает модель с инструментами, обрабатывает вызовы инструментов и сохраняет состояние сессии."""
# Agent — это “модель + память + инструменты”.
class Agent:
    """
    В __init__:
    сохраняет instruction — системную подсказку для модели,
    сохраняет model, сохраняет tool_choice, строит tool_map:
    из tools берутся только классы, унаследованные от BaseModel,
    создаётся словарь вида { "ListExercises": ListExercisesClass, ... }
    создаёт self.tools — список схем инструментов через _create_tool_annot(...)
    создаёт self.user_sessions для хранения состояния между сообщениями
    """
    def __init__(self, instruction, tools=None, model=None, tool_choice="auto"):
        self.instruction = instruction
        self.model = model
        self.tool_choice = tool_choice
        self.tools = tools or []
        self.tool_map = {
            x.__name__: x
            for x in self.tools
            if not isinstance(x, dict) and issubclass(x, BaseModel)
        }
        self.api_tools = [_create_tool_annot(x) for x in self.tools]
        self.user_sessions = {}

    """
    В __call__(message, session_id='default'):
    берет состояние пользователя из self.user_sessions
    добавляет сообщение пользователя в history
    вызывает:
    с параметрами:
    model=self.model
    tools=self.tools
    instructions=self.instruction
    input=message
    previous_response_id=...
    store=True
    """
    def __call__(self, message, session_id="default"):
        """Обрабатывает сообщение пользователя и вызывает функции при необходимости."""
        s = self.user_sessions.get(
            session_id,
            {"previous_response_id": None, "history": []},
        )
        s["history"].append({"role": "user", "content": message})

        res = client.responses.create(
            model=self.model,
            store=True,
            tools=self.api_tools,
            tool_choice=self.tool_choice,
            instructions=self.instruction,
            previous_response_id=s["previous_response_id"],
            input=message,
        )

        tool_calls = [
            item for item in res.output
            if item.type == "function_call" and item.name in self.tool_map
        ]
        if tool_calls:
            s["history"].append({"role": "func_call", "content": res.output_text})
            out = []
            for call in tool_calls:
                try:
                    fn = self.tool_map[call.name]
                    args = call.arguments or "{}"
                    obj = fn.model_validate(json.loads(args))
                    result = obj.process(session_id)
                except Exception as e:
                    result = f"Ошибка: {e}"

                out.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": result,
                    }
                )

                res = client.responses.create(
                    model=self.model,
                    input=out,
                    tools=self.api_tools,
                    previous_response_id=res.id,
                    store=True,
                )
        print("STATUS:", res.status)
        print("ERROR:", res.error)
        if res.status == "incomplete":
            print(f"WARNING: Incomplete response status. Reason={res.incomplete_details.reason}")
        else:
            s["previous_response_id"] = res.id

        s["history"].append({"role": "assistant", "content": res.output_text})
        self.user_sessions[session_id] = s
        return res


web_search_tool = {"type": "web_search"}

instruction = """
Ты — опытный фитнес-тренер, задача которого — помочь мне тренироваться в зале. Ты можешь
советовать упражнения, давать рекомендации по питанию и т. д. Отвечай на основе имеющейся
дополнительной информации из файловой базы знаний, вызывая инструмент поиска `search_tool`.
В случае если запрос касается упоминания абстрактных фитнес-клубов или новостей, используй
поиск в интернет `web_search_tool`.
Ты также можешь вести дневник выполненных пользователем упражнений — для этого используй
функцию `Exercise`. Чтобы показать список выполненных упражнений, используй `ListExercises`.

Ты также можешь вести заметки с помощью MCP-сервера `PersonalNotes`.
Для дневника тренировок используй блокнот "Упражнения".
"""

def run_demo():
    # Собираем список инструментов: сначала внешние (dict) инструменты, затем Python-модели
    tools = []

    # web_search_tool — всегда доступен
    tools.append(web_search_tool)
    # MCP-сервер погоды
    tools.append(weather_tool)
    # MCP-сервер заметок
    tools.append(notes_tool)

    # search_tool доступен, когда в проекте создан vector_store
    if search_tool is not None:
        tools.append(search_tool)

    # Добавляем наши Pydantic-инструменты
    tools.extend([Exercise, ListExercises])

    fit_agent = Agent(
        instruction,
        tools=tools,
        model=model,
        tool_choice="required",
    )

    # Примеры взаимодействия
    response = fit_agent("Я сделал 25 приседаний, запиши!")
    print(response.output_text)

    response = fit_agent("Напомни, какие я сделал упражнения?")
    print(response.output_text)

    # Пример запроса, когда модель должна использовать web_search_tool
    response = fit_agent(
        "Сколько стоит годовой абонемент в фитнес-клуб в Санкт-Петербурге?"
    )
    print(response.output_text)

    # Тестирование MCP-сервера заметок
    response = fit_agent(
        'Добавь в блокнот "Упражнения" заметку: "Сегодня сделал 25 приседаний".'
    )
    print(response.output_text)

    response = fit_agent(
        'Покажи мои заметки из блокнота "Упражнения"'
    )
    print(response.output_text)

    
    response = fit_agent("Стоит ли сегодня побегать на улице в Москве? Проверь погоду.")
    print(response.output_text)

if __name__ == "__main__":
    run_demo()

