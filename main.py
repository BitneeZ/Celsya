from init_llm import init_model
from generate_roadmap import generate_roadmap_json
from to_json import to_json

MODEL_ID = "Qwen/Qwen3-4B"
TOPIC = 'Изучение веб-разработки'


if __name__=='__main__':
    model, tokenizer = init_model(MODEL_ID)

    output = generate_roadmap_json(model, tokenizer,
                                   TOPIC, 500)
    
    to_json(TOPIC, output)