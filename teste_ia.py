import asyncio
import sys
from loguru import logger
from src.core.ai_brain import AIProcessor

# Configuração simples de log para o teste
logger.remove()
logger.add(sys.stderr, format="<level>{message}</level>")


async def testar_cerebro():
    print("🧠 INICIALIZANDO CÉREBRO DA IA...\n")
    try:
        brain = AIProcessor()
        if not brain.model:
            print("❌ ERRO: A IA não conectou. Verifique sua GEMINI_API_KEY no .env")
            return
    except Exception as e:
        print(f"❌ Erro ao iniciar: {e}")
        return

    # CENÁRIOS DE TESTE
    cenarios = [
        {
            "tipo": "✅ COMPLETO (Preço Antigo + Cupom)",
            "texto": "Smartphone Samsung Galaxy S23 Ultra. De R$ 8.000,00 por apenas R$ 5.999,00 usando o cupom GALAXY200 no carrinho!"
        },
        {
            "tipo": "⚠️ SEM 'DE' (Não pode inventar valor antigo)",
            "texto": "Fritadeira Air Fryer Mondial 4L. Melhor preço do dia: R$ 299,90 à vista na Amazon. Aproveite."
        },
        {
            "tipo": "🎮 CASO PS5 (Texto confuso)",
            "texto": "Console PlayStation 5 Edição Digital Slim. Inclui 2 jogos. Valor final R$ 3.500 em até 10x sem juros. Frete Grátis."
        }
    ]

    for i, cenario in enumerate(cenarios, 1):
        print(f"--- TESTE {i}: {cenario['tipo']} ---")
        print(f"📥 Texto Original: \"{cenario['texto']}\"")
        print("⏳ Gerando...")

        # Chama a IA simulando que veio da AMAZON
        resultado = await brain.gerar_legenda(cenario['texto'], "AMAZON")

        print("\n📤 RESPOSTA DA IA (Como vai ficar no Zap):")
        print("=" * 40)
        print(resultado)
        print("=" * 40)
        print("\n")
        await asyncio.sleep(2)  # Pequena pausa para não estourar limite no teste


if __name__ == "__main__":
    asyncio.run(testar_cerebro())