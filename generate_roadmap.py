import json
from json_repair import repair_json
from prompts import ROADMAP_PROMPT

def generate_roadmap_json(model, 
                          topic: str, max_tokens=512) -> dict:
    prompt = ROADMAP_PROMPT.replace('topic', topic) 

    output = model(
        prompt,
        max_tokens=max_tokens,
        temperature=0.7,
        stop=["</s>"]
    )

    text_output = output["choices"][0]["text"].strip()

    # Вырезаем только JSON
    json_start = text_output.find("[")
    json_end = text_output.rfind("]") + 1
    json_text = text_output[json_start:json_end] if json_start != -1 else "[]"

    # Чиним JSON если нужно
    return json_text

