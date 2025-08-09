from transformers import AutoTokenizer, AutoModelForCausalLM
from llama_cpp import Llama
from json_repair import repair_json
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

def new_init_model(model):
    llm = Llama(
        model_path=model,
        n_threads=6,
        n_ctx=2048
    )
    return llm

