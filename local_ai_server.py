from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Khặn lỗi PyTorch classes
torch.classes.__path__ = []

app = FastAPI()

print("⏳ Đang nạp mô hình Qwen2.5-1.5B-Instruct vào RAM cho Local AI Server...")
model_id = "Qwen/Qwen2.5-1.5B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    dtype=torch.bfloat16,
    low_cpu_mem_usage=True
)
print("✅ Local AI Server đã sẵn sàng!")

class PromptRequest(BaseModel):
    prompt: str
    system_instruction: str = ""

@app.post("/generate")
def generate_text(req: PromptRequest):
    try:
        messages = [
            {"role": "system", "content": req.system_instruction},
            {"role": "user", "content": req.prompt}
        ]
        
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = tokenizer([prompt], return_tensors="pt")
        input_length = inputs.input_ids.shape[1]

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )

        generated_ids = outputs[0][input_length:]
        reply_text = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

        return {"reply": reply_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Chạy đúng vào cổng 9000 đang thông với MinIO/Tunnel của bạn
    uvicorn.run(app, host="127.0.0.1", port=9000)