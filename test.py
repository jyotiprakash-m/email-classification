import requests
import json

response = requests.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": "Bearer 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",
    "Content-Type": "application/json",
  },
  data=json.dumps({
    "model": "qwen/qwq-32b:free",
    "messages": [
      {
        "role": "user",
        "content": "What is the meaning of life?"
      }
    ],
    
  })
)

print(response.json())