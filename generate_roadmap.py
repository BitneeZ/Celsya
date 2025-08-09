import json
from json_repair import repair_json
from prompts import ROADMAP_PROMPT

def generate_roadmap_json(model, tokenizer,
                          topic:str, max_tokens=64):
    prompt = ROADMAP_PROMPT.replace('topic', topic) 
    messages = [
        {"role": "user", "content": prompt}
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False
    )
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

    # conduct text completion
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=max_tokens
    )
    output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist() 

    # parsing thinking content
    try:
        # rindex finding 151668 (</think>)
        index = len(output_ids) - output_ids[::-1].index(151668)
    except ValueError:
        index = 0

    # thinking_content = tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip("\n")
    content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")
    
    # json_start = content.find("[")
    # json_end = content.rfind("]") + 1
    # return content[json_start:json_end]
    return content

def new_generate_roadmap_json(model, 
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
    # try:
    #     roadmap_data = json.loads(json_text)
    # except json.JSONDecodeError:
    #     roadmap_data = json.loads(repair_json(json_text))

    # return {
    #     "topic": topic,
    #     "roadmap": roadmap_data
    # }

