# import requests
# import os



# def llm_client(prompt: str):

#     response = requests.post(
#         "https://api.x.ai/v1/chat/completions",
#         headers={
#             "Authorization": f"Bearer {GROK_API_KEY}",
#             "Content-Type": "application/json"
#         },
#         json={
#             "model": "grok-2-latest",
#             "messages": [{"role": "user", "content": prompt}],
#             "temperature": 0
#         },
#         timeout=30
#     )

#     if response.status_code != 200:
#         raise Exception(f"Grok API error: {response.text}")

#     data = response.json()

#     return data["choices"][0]["message"]["content"]