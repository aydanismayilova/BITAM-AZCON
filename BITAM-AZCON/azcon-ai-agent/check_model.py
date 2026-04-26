import google.generativeai as genai
import os
from dotenv import load_dotenv

# .env faylındakı API kodunu oxuyuruq
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

print("Sizin API Key-in dəstəklədiyi (generateContent) modellərin siyahısı:\n" + "-"*50)

# Google-dan dəstəklənən modelləri çəkirik
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
