from qwen_class import QwenChatbot

QWEN3_4B = "Qwen/Qwen3-4B"
QWEN_Q_GGUF = "C:/Users/Redmi/.lmstudio/models/lmstudio-community/Qwen3-4B-GGUF/Qwen3-4B-Q4_K_M.gguf"
TOPIC = 'Изучение веб-разработки'


if __name__=='__main__':
    model = QwenChatbot(QWEN_Q_GGUF)

    model.generate_response(TOPIC, 512)
    model.to_json(TOPIC)

    print(f'RESULT: {model.last_output}')