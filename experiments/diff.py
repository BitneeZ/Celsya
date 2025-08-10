#pip install git+https://github.com/huggingface/diffusers

from diffusers import DiffusionPipeline
import torch

# Модель
model_name = "Qwen/Qwen-Image"

if torch.cuda.is_available():
    torch_dtype = torch.bfloat16
    device = "cuda"
else:
    torch_dtype = torch.float32
    device = "cpu"

pipe = DiffusionPipeline.from_pretrained(model_name, torch_dtype=torch_dtype)
pipe = pipe.to(device)

# Промпт
prompt = "Кот в шляпе"

# Сгенерация изображения
image = pipe(prompt=prompt).images[0]

# Сохранение изображения
image.save("cat_in_a_hat.png")