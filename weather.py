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

weather_tool = {
    "type": "mcp",
    "server_label": "weather",
    "server_url": "https://db84j3q6965uu56u0e5p.fi4781wp.mcpgw.serverless.yandexcloud.net/sse",
    "require_approval": "never",
}

def run_demo():
    res = client.responses.create(
        model=model,
        tools=[weather_tool],
        input="Какая погода в Москве?",
    )

    print(res.output_text)

    for x in res.output:
        if x.type=='mcp_call':
            print(f" + Вызов {x.name}{x.arguments}")
            print(f"   Результат: {x.output}")

    #for item in res.output:
    #   print(item)


if __name__ == "__main__":
    run_demo()