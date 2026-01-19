import google.generativeai as genai
from groq import Groq
from loguru import logger
from src.config.settings import config
import asyncio


class AIProcessor:
    def __init__(self):
        # 1. Configuração GEMINI (Titular)
        self.gemini_ok = False
        if config.GEMINI_API_KEY:
            try:
                genai.configure(api_key=config.GEMINI_API_KEY)
                # Modelo Flash 2.5 (Rápido e Gratuito)
                self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
                self.gemini_ok = True
            except Exception as e:
                logger.error(f"❌ Erro ao iniciar Gemini: {e}")

        # 2. Configuração GROQ (Reserva)
        self.groq_client = None
        if config.GROQ_API_KEY:
            try:
                self.groq_client = Groq(api_key=config.GROQ_API_KEY)
                logger.success("🤖 Cérebro Híbrido: Gemini + Groq (Backup) Ativados!")
            except Exception as e:
                logger.error(f"❌ Erro ao iniciar Groq: {e}")
        else:
            logger.warning("⚠️ GROQ_API_KEY não encontrada. Backup desativado.")

    async def gerar_legenda(self, texto_original: str, loja: str) -> str:
        prompt = self._construir_prompt(texto_original)

        # TENTATIVA 1: GEMINI (Titular)
        if self.gemini_ok:
            try:
                # Segurança mínima para não bloquear bobeira
                safety = [{"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]
                response = await self.gemini_model.generate_content_async(prompt, safety_settings=safety)
                return self._limpar_resposta(response.text)
            except Exception as e:
                logger.warning(f"⚠️ Gemini falhou/cota cheia ({e}). Acionando Groq...")

        # TENTATIVA 2: GROQ (Reserva de Luxo)
        if self.groq_client:
            try:
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "Você é um Copywriter Especialista em Black Friday."
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    # MUDANÇA AQUI: Modelo atualizado e vigente na Groq
                    model="llama-3.3-70b-versatile",
                    temperature=0.7,
                )
                return self._limpar_resposta(chat_completion.choices[0].message.content)
            except Exception as e:
                logger.error(f"❌ Groq também falhou: {e}")

        # TENTATIVA 3: FALLBACK (Se o mundo acabar)
        return self._fallback_legenda(loja)

    def _construir_prompt(self, texto: str) -> str:
        return f"""
        ATUE COMO UM LOCUTOR DE OFERTAS "VENDEDOR AGRESSIVO".
        Transforme os dados abaixo em uma mensagem EXPLOSIVA para WhatsApp.

        ESTILO OBRIGATÓRIO:
        1. TÍTULO EM CAPSLOCK (CAIXA ALTA) COM EMOJIS DE ALERTA.
        2. Use emojis no início de TODAS as linhas.
        3. Destaque o preço com "💰" ou "✅".
        4. Crie SENSO DE URGÊNCIA no final.

        LAYOUT DE SAÍDA (Siga rigorosamente):

        🚨 [TÍTULO CURTO E GRITANTE EM CAPSLOCK] 🚨

        📦 *[Nome do Produto]*

        ❌ De: ~R$ valor antigo~ (SOMENTE se houver valor antigo explícito. Se não, NÃO INVENTE!)
        ✅ Por: *R$ valor atual* (Destaque o valor final)

        🎟️ Cupom: *CODIGO* (SOMENTE se houver cupom. Se não, NÃO INVENTE!)

        🔥 *CORRA! ESTOQUE LIMITADO!* 🏃‍♂️💨

        TEXTO ORIGINAL:
        "{texto}"
        """

    def _limpar_resposta(self, texto: str) -> str:
        """Remove markdown de código que as IAs colocam"""
        return texto.replace("```", "").replace("**Title:**", "").strip()

    def _fallback_legenda(self, loja: str) -> str:
        return f"🚨 *OFERTA IMPERDÍVEL NA {loja.upper()}!* 🚨\n\n😱 *PREÇO BAIXOU! APROVEITE AGORA!*\n\n🔥 *Corra antes que acabe!*"