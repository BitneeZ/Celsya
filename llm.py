from llama_cpp import Llama
from json_repair import repair_json
import json
from prompts import ROADMAP_PROMPT

# Загружаем GGUF-модель

llm = Llama(
	model_path="./models/qwen2.5-1.5b-instruct-fp16.gguf", 
    n_threads=4,           # подбери под количество ядер CPU
    n_ctx= 4096
)

def generate_roadmap_json(topic: str, max_tokens = 2048) -> dict:
    prompt = ROADMAP_PROMPT.format(topic=topic)

    output = llm(
        prompt,
        max_tokens=max_tokens,
        temperature=0.7,
        stop=["</s>", "<|eot_id|>"] 
    )

    text_output = output["choices"][0]["text"].strip()

    # Вырезаем только JSON
    json_start = text_output.find("[")
    json_end = text_output.rfind("]") + 1
    json_text = text_output[json_start:json_end] if json_start != -1 else "[]"

    # Чиним JSON если нужно
    try:
        roadmap_data = json.loads(json_text)
    except json.JSONDecodeError:
        roadmap_data = json.loads(repair_json(json_text))

    return {
        "topic": topic,
        "roadmap": roadmap_data
    }