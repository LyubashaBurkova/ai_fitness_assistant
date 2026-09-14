from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("YANDEX_API_KEY") or os.getenv("api_key")
folder_id = os.getenv("FOLDER_ID") or os.getenv("folder_id")

client = OpenAI(
   base_url = "https://ai.api.cloud.yandex.net/v1",
   api_key = api_key,
   project = folder_id
)

model = f"gpt://{folder_id}/qwen3-235b-a22b-fp8/latest"

instructions = """
Ты — профессиональный фитнес-ассистент. Отвечай как энергичный молодой 
человек со спортивным задором.
"""

res_1 = client.responses.create(
    model=model,
    input="Как тренироваться, чтобы сбросить вес?"
)

res_2 = client.responses.create(
    model = model,
    input = [
    { 
      "role": "system", 
      "content": "Ты — опытный фитнес-тренер, задача которого — помочь мне тренироваться в зале." 
    },
    { 
      "role": "user", 
      "content": "Привет! С чего ты порекомендуешь начать тренировки в зале?" 
    }
])

res_3 = client.responses.create(
    model = model,
    instructions = "Ты — опытный фитнес-тренер, задача которого — помочь мне тренироваться в зале.",
    input = "Привет! С чего ты порекомендуешь начать тренировки в зале?" 
)

res_4 = client.responses.create(
    model = model, 
    store = True,
    instructions = instructions,
    input = "Как тренироваться, чтобы сбросить вес?"
)

res = client.responses.create(
    model = model,
    store = True,
    instructions = instructions,
    previous_response_id = res.id,
    input = "Мне нужен пошаговый план тренировки. Мой рост — 180, вес — 75 кг."
)


print(res.output_text)