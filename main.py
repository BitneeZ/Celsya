from init_llm import init_model, new_init_model
from generate_roadmap import generate_roadmap_json, new_generate_roadmap_json
from to_json import to_json, new_to_json

QWEN3_4B = "Qwen/Qwen3-4B"
QWEN_Q_GGUF = "C:/Users/Redmi/.lmstudio/models/lmstudio-community/Qwen3-4B-GGUF/Qwen3-4B-Q4_K_M.gguf"
TOPIC = 'Изучение веб-разработки'


if __name__=='__main__':
    # model, tokenizer = init_model(MODEL_ID)
    # output = generate_roadmap_json(model, tokenizer,
    #                                TOPIC, 500)
    # to_json(TOPIC, output)

    model = new_init_model(QWEN_Q_GGUF)

    content = new_generate_roadmap_json(model, TOPIC, 512)

    new_to_json(TOPIC, content)