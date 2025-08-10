from transformers import AutoTokenizer, AutoModelForCausalLM
from llama_cpp import Llama
from json_repair import repair_json
import json

def init_model(model):
    llm = Llama(
        model_path=model,
        n_threads=6,
        n_ctx=2048
    )
    return llm

