import google.generativeai as genai
from src.config.settings import config
import os


def check():
    print("🔍 Verificando modelos disponíveis para sua API Key...\n")

    if not config.GEMINI_API_KEY:
        print("❌ ERRO: Adicione GEMINI_API_KEY no seu .env")
        return

    genai.configure(api_key=config.GEMINI_API_KEY)

    try:
        modelos_validos = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ Disponível: {m.name}")
                modelos_validos.append(m.name)

        if not modelos_validos:
            print("\n❌ NENHUM modelo de geração de texto encontrado para esta chave.")
            return

        modelo_escolhido = modelos_validos[0]
        print(f"\n🧪 Testando geração com: {modelo_escolhido} ...")

        model = genai.GenerativeModel(modelo_escolhido)
        response = model.generate_content("Responda apenas: 'IA Funcionando!'")

        print(f"🎉 SUCESSO! Resposta da IA: {response.text}")
        print(f"\n👉 Para consertar seu bot, copie o nome '{modelo_escolhido}' (sem 'models/') e coloque no ai_brain.py")

    except Exception as e:
        print(f"\n❌ Erro crítico ao listar modelos: {e}")


if __name__ == "__main__":
    check()