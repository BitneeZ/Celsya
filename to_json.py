import json

def to_json(topic, content):
    try:
        roadmap_data = json.loads(content)
    except json.JSONDecodeError:
        print("Ошибка: модель вернула некорректный JSON")
        with open('wrong_format_output.txt', 'w') as f:
            f.write(content)
            print(f'ERROR DAMN: {content}')
        roadmap_data = []

    print(json.dumps({
        "topic": topic,
        "roadmap": roadmap_data
    }, ensure_ascii=False, indent=2))