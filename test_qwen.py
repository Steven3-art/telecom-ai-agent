import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    api_key=os.getenv("QWEN_API_KEY"),
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)

response = client.chat.completions.create(
    model="qwen-plus",
    messages=[
        {
            "role": "user",
            "content": "Tu es un agent de support FTTH. Dis bonjour en 1 phrase."
        }
    ]
)

print("✅ Connexion Qwen réussie !")
print(f"Réponse : {response.choices[0].message.content}")