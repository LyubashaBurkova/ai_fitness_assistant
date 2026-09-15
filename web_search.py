from __future__ import annotations

import json
import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

api_key = os.getenv("YANDEX_API_KEY") or os.getenv("api_key")
folder_id = os.getenv("FOLDER_ID") or os.getenv("folder_id")

client = OpenAI(
    base_url="https://ai.api.cloud.yandex.net/v1",
    api_key=api_key,
    project=folder_id,
)

model = f"gpt://{folder_id}/qwen3-235b-a22b-fp8/latest"
#Пример запроса для поиска через веб ресурсы "web_search" 

res_ws = client.responses.create(
    model = model,
    instructions = system_prompt,
    tools = [ { "type": "web_search" } ],
    input = "Сколько в среднем стоит годовой абонемент на занятия в фитнес-клубе в Москве?"
)


print(f"Ответ без поиска: {len(res.output)}") # напечатает 1
print(f"Ответ с поиском: {len(res_ws.output)}") # напечатает 2

#previous_response_id = res_ws.id, для сохранения контекста

res_ws_2 = client.responses.create(
    model = model,
    previous_response_id = res_ws.id,
    tools = [ { "type": "web_search" } ],
    input = "А поищи самый дешёвый?"
)

print(res_ws_2.output_text) 


#с учетом фильтров по домену и региону:
response = client.responses.create(
    model=model,
    input="Сделай краткий обзор отзывов на World Class Fitness",
    tools=[
        {
            "type": "web_search",
            "filters": {
                "allowed_domains": [
                    "otzovik.com"
                ],
                "user_location": {
                    "region": "213", # Москва
                },
            },
            "search_context_size": "medium", # варианты: low | medium | high
        }
    ]
)
print(response.output_text)