import os
import json
import time
from abc import ABC, abstractmethod
from openai import OpenAI
import google.generativeai as genai

class Client(ABC):
    def __init__(self):
        # 專案根目錄下的 java/ 專案共用同一份 config.json（執行時的工作目錄需為專案根目錄）
        self.config_path = os.path.join("java", "src", "main", "resources", "config.json") # API 檔案路徑

    def _load_api_key(self, OPENAI_API_KEY) -> str:
        with open(self.config_path, "r") as file:
            config = json.load(file)
        if OPENAI_API_KEY == "openAI":
            api_key = config.get("OPENAI_API_KEY")
        elif OPENAI_API_KEY == "gemini":
            api_key = config.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Error: API Key not found in config.json")
        return api_key

    @abstractmethod
    def execute_query(self, prompt: str, **kwargs) -> str:
        """執行查詢，由子類別實現"""
        pass


class ChatGPTClient(Client):
    def __init__(self, model_name: str):
        super().__init__()
        self.api_key = super()._load_api_key("openAI")
        self.model_name = model_name
        self.client = OpenAI(
            api_key = self.api_key
        )
        
    def execute_query(
        self,
        prompt: str,
        max_completion_tokens: int = 1200,
        temperature: float = 1.0,
        top_p: float = 1.0,
        n: int = 1,
        stream: bool = False, # 回應一次性生成並返回
        stop: str = None,
        presence_penalty: float = 0.6,
        frequency_penalty: float = 0.3,
        user: str = None,
        logit_bias: dict = None,
    ) -> str:
        params = {
            "messages": [{"role": "user", "content": prompt}],
            "model": self.model_name,
            "max_completion_tokens": max_completion_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "n": n,
            "stream": stream,
            "stop": stop,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "user": user,
            "logit_bias": logit_bias,
        }

        # 過濾掉不支援的參數
        if self.model_name.startswith("o1"):
            unsupported_keys = [
                "temperature",
                "top_p",
                "presence_penalty",
                "frequency_penalty",
                "logit_bias"
            ]
            for k in unsupported_keys:
                if k in params:
                    params.pop(k, None)

        """執行查詢並返回結果"""
        start_time = time.time()
        chat_completion = self.client.chat.completions.create(
            **params
        )
        end_time = time.time()
        print(f"Query Time: {end_time - start_time:.2f} seconds")
        print("Total Tokens:", chat_completion.usage.total_tokens)
        return chat_completion.choices[0].message.content


class GeminiClient(Client):
    def __init__(self, model_name: str):
        super().__init__()
        self.api_key = super()._load_api_key("gemini")
        genai.configure(api_key = self.api_key) 
        self.model = genai.GenerativeModel(model_name)

    def execute_query(
        self,
        prompt: str,
        max_output_tokens: int = 1000,
        temperature: float = 1,
        top_p: float = 1.0,
        top_k: int = 1,
        candidate_count: int = 1
    ) -> str:
        """執行查詢並返回結果"""
        start_time = time.time()
        response = self.model.generate_content(
            prompt,
            generation_config = genai.GenerationConfig(
                max_output_tokens = max_output_tokens,
                temperature = temperature,
                top_p = top_p,
                top_k = top_k,
                candidate_count = candidate_count
            )
        )
        end_time = time.time()
        print(f"Query Time: {end_time - start_time:.2f} seconds")
        print("Total Tokens:", response.usage_metadata.total_token_count)
        return response.text


def main():
    # 設定 LLM 參數
    prompt = "Say this is a test."
    max_tokens = 1000
    temperature = 1

    client = ChatGPTClient(model_name = "gpt-4o")
    # client = GeminiClient(model_name = "gemini-1.5-pro")

    response = client.execute_query(prompt, max_tokens, temperature)
    print("Response:\n", response)


if __name__ == "__main__":
    main()
