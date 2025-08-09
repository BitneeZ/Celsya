from transformers import AutoTokenizer, AutoModelForCausalLM
import json

def init_model(model):
    # load the tokenizer and the model
    tokenizer = AutoTokenizer.from_pretrained(model)
    model = AutoModelForCausalLM.from_pretrained(
        model,
        torch_dtype="auto",
        device_map="auto"
    )
    return model, tokenizer

