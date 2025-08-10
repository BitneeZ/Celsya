from llama_cpp import Llama
from json_repair import repair_json
import json
from prompts import ROADMAP_PROMPT

class QwenChatbot:
    def __init__(self, model_name):
        self.model = Llama(
            model_path=model_name,
            n_threads=6,
            n_ctx=2048
        )
        self.last_output = ''

    def generate_response(self, topic, max_tokens=512):
        prompt = ROADMAP_PROMPT.replace('topic', topic) 

        output = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=0.7,
            stop=["</s>"]
        )

        #? что делает
        self.last_output = output["choices"][0]["text"].strip()
    
    def to_json(self, topic):
        json_start = self.last_output.find("[")
        json_end = self.last_output.rfind("]") + 1
        json_text = self.last_output[json_start:json_end] if json_start != -1 else "[]"

        try:
            roadmap_data = json.loads(json_text)
        except json.JSONDecodeError:
            print("Ошибка: модель вернула некорректный JSON")
            with open('wrong_format_output.txt', 'w', encoding='utf-8') as f:
                f.write(json_text)
            
            roadmap_data = json.loads(repair_json(json_text))

        self.last_output = json.dumps({
            "topic": topic,
            "roadmap": roadmap_data
        }, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    MODEL = 'C:/Users/Redmi/.lmstudio/models/lmstudio-community/Qwen3-4B-GGUF/Qwen3-4B-Q4_K_M.gguf'
    chatbot = QwenChatbot(model_name=MODEL)

    response1 = 'Изучение веб-разработки'
    chatbot.generate_response(response1, 512)
    chatbot.to_json(response1)

    print(f'RESULT: {chatbot.last_output}')