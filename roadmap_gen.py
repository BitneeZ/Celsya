from llm import generate_roadmap_json
import json

#pip install llama-cpp-python json-repair

if __name__ == "__main__":
    topic = 'Научиться работать с игровым движком UnrealEngine5'
    result = generate_roadmap_json(topic)
    print(json.dumps(result, ensure_ascii=False, indent=2))
