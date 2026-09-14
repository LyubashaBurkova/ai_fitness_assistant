import json

from fitness_service import (
    calculate_calories,
    call_model,
    get_exercise_history,
    get_weight_history,
    log_exercise,
    log_weight,
)


if __name__ == "__main__":
    prompt = "Я сегодня сделал 3 подхода по 12 приседаний с весом 70 кг. Сегодня мой вес 45 кг."
    response = call_model(prompt, user_id="default")

    for item in response.output:
        if item.type == "function_call":
            name = item.name
            args = json.loads(item.arguments)

            if name == "log_exercise":
                result = log_exercise(**args)
                print(result["message"])

            elif name == "log_weight":
                result = log_weight(**args)
                print(result["message"])

            elif name == "get_exercise_history":
                result = get_exercise_history(**args)
                print(result)

            elif name == "get_weight_history":
                result = get_weight_history(**args)
                print(result)

            elif name == "calculate_calories":
                result = calculate_calories(**args)
                print(result)
