from init_llm import init_model
from generate_roadmap import generate_roadmap_json
from to_json import to_json

QWEN3_4B = "Qwen/Qwen3-4B"
QWEN_Q_GGUF = "C:/Users/Redmi/.lmstudio/models/lmstudio-community/Qwen3-4B-GGUF/Qwen3-4B-Q4_K_M.gguf"
TOPIC = 'Изучение веб-разработки'


if __name__=='__main__':
    model = init_model(QWEN_Q_GGUF)

    content = generate_roadmap_json(model, TOPIC, 512)

    to_json(TOPIC, content)