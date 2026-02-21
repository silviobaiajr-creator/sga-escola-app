import google.generativeai as genai
import os

# Load key from secrets or environment
# For this script we'll use the key directly provided earlier for testing
api_key = "AIzaSyDZwZdoUeEvLlSoeK75NW_XqOMEfSb9xS4"

genai.configure(api_key=api_key)

print("Listando modelos disponíveis...")
try:
    with open("models.txt", "w", encoding="utf-8") as f:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                f.write(f"Nome: {m.name}\n")
    print("Concluído!")
except Exception as e:
    print(f"Erro: {e}")
