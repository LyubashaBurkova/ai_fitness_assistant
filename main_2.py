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


class Assistant:
    def __init__(self, instructions, model=model):
        self.model = model
        self.instructions = instructions
        self.previous_response_id_map = {}

    def __call__(self, input, session_id='default'):
        # Получите ID предыдущего сообщения для данной сессии
        previous_response_id = self.previous_response_id_map.get(session_id, None)

        # Сформируйте ответ модели
        res = client.responses.create(
            model = self.model,
            store = True,
            previous_response_id = previous_response_id,
            instructions = self.instructions,
            input = input
        )
        # Запомните ID последнего ответа модели в словаре
        self.previous_response_id_map[session_id] = res.id
        return res.output_text

instructions = """
Ты — профессиональный фитнес-ассистент. Отвечай как энергичный молодой человек 
со спортивным задором. Говори как человек, короткими фразами, избегая 
перечислений и списков.
"""

assistant = Assistant(instructions)

print(assistant("Привет! С чего ты порекомендуешь начать тренировки в зале?"))

print(assistant("Я хочу похудеть!"))
 