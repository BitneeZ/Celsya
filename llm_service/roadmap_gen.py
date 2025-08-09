from llm import generate_roadmap_json
import json

#pip install llama-cpp-python json-repair

if __name__ == "__main__":
    topic = "Изучение веб-разработки"
    result = generate_roadmap_json(topic)
    print(json.dumps(result, ensure_ascii=False, indent=2))
