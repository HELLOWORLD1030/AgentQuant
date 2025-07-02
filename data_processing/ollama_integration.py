import re

import ollama
from config import Config


class Qwen3Model:
    def __init__(self):
        self.model_name = Config.QWEN_MODEL
        self.client = ollama.Client(host=Config.OLLAMA_HOST)

    def generate_response(self, prompt, history=None, max_tokens=2000):
        """使用Qwen3生成响应"""
        messages = []

        # 添加历史对话
        if history:
            for msg in history:
                messages.append({
                    "role": "user" if msg["role"] == "user" else "assistant",
                    "content": msg["content"]
                })

        # 添加当前提示
        messages.append({"role": "user", "content": prompt})

        # 调用Ollama API
        response = self.client.chat(
            model=self.model_name,
            messages=messages,
            options={
                "num_predict": max_tokens,
                "temperature": 0.3
            }
        )
        raw_output = response["message"]["content"]
        clean_output = re.sub(r"<think>.*?</think>", "", raw_output, flags=re.DOTALL).strip()
        return clean_output