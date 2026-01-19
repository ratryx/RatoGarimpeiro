import asyncio
import re
import sys
import os
import time
from telethon import TelegramClient, events
from loguru import logger
import tweepy
from src.config.settings import config
from src.config.constants import CANAIS_FONTE
from src.core.ai_brain import AIProcessor
from src.core.link_router import LinkRouter
from src.infrastructure.whatsapp_client import whatsapp_client
from src.core.amazon_image import baixar_imagem_amazon

# Configuração de Log Scannable
logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>")
logger.add("logs/sanguessuga.log", rotation="1 day", retention="7 days")

logger.info("🐭 RATO GARIMPEIRO (MODO AGRESSIVO) ATIVADO!")

# Inicialização de Componentes
try:
    client = TelegramClient('sanguessuga_session.session', config.API_ID, config.API_HASH)
    ai_brain = AIProcessor()
    link_router = LinkRouter()
    fila_postagem = asyncio.Queue()  # Fila para evitar flood
    logger.success("✅ Core OK!")
except Exception as e:
    logger.critical(f"❌ Erro Inicial: {e}")
    sys.exit(1)

# Configuração Twitter/X
client_x = None
twitter_blocked_until = 0  # Controle de castigo do Twitter

if config.X_API_KEY:
    try:
        client_x = tweepy.Client(
            consumer_key=config.X_API_KEY, consumer_secret=config.X_API_SECRET,
            access_token=config.X_ACCESS_TOKEN, access_token_secret=config.X_ACCESS_TOKEN_SECRET
        )
        logger.success("🐦 X OK!")
    except Exception as e:
        logger.error(f"🐦 X Off: {e}")

links_processados = []
posts_twitter_hoje = 0


# --- FUNÇÕES DE APOIO ---

async def resolve_safe_channels():
    """Valida se os canais fonte existem no Telegram"""
    valid_channels = []
    for channel_name in list(CANAIS_FONTE):
        try:
            await client.get_input_entity(channel_name)
            valid_channels.append(channel_name)
        except Exception:
            logger.error(f"❌ Ignorado: {channel_name}")
    return valid_channels


async def trabalhador_da_fila():
    """
    Consome a fila.
    A MÁGICA ACONTECE AQUI: A IA só é chamada 1 vez a cada 3 minutos.
    Isso impede que sua conta do Google seja bloqueada por excesso de pedidos.
    """
    global posts_twitter_hoje, twitter_blocked_until

    while True:
        # Pega os dados crus da fila
        oferta = await fila_postagem.get()
        try:
            # Note que agora pegamos 'texto_puro' e não 'legenda'
            texto_puro, link, foto, loja = oferta

            logger.info(f"🤖 Gerando legenda 'Vendedor Agressivo' para: {loja}...")

            # --- GERAÇÃO DE LEGENDA (MOMENTO SEGURO) ---
            # Aqui chamamos a IA. Como o loop tem sleep de 180s,
            # nunca faremos mais requisições do que o Google permite.
            legenda = await ai_brain.gerar_legenda(texto_puro, loja)

            logger.info(f"🚀 Enviando oferta processada: {loja}")

            # 1. Envio WhatsApp
            sucesso_wa, status_code = await whatsapp_client.enviar_oferta(legenda, link, foto)

            if sucesso_wa:
                logger.success(f"📱 WhatsApp OK! (Fila: {fila_postagem.qsize()} restantes)")
            else:
                logger.error(f"❌ Erro WA (Status: {status_code})")
                if status_code == 401:
                    await client.send_message(config.ADMIN_USER, "⚠️ Token UAZAPI Expirou!")

            # 2. Envio Twitter/X (Com proteção Anti-429)
            if client_x and posts_twitter_hoje < config.LIMITE_DIARIO_X:
                if time.time() > twitter_blocked_until:
                    try:
                        # Cria um tweet resumido
                        tweet_txt = f"{legenda[:200]}...\n\n🛒: {link}\n\n#promo #oferta"
                        client_x.create_tweet(text=tweet_txt)
                        posts_twitter_hoje += 1
                        logger.success("🐦 Tweet enviado!")
                    except Exception as e:
                        error_msg = str(e)
                        if "429" in error_msg or "Too Many Requests" in error_msg:
                            logger.warning("⛔ Twitter 429 (Muitas requisições). Pausando X por 30min.")
                            twitter_blocked_until = time.time() + 1800
                        else:
                            logger.warning(f"🐦 Erro Twitter: {e}")
                else:
                    logger.info("⏳ Twitter em cooldown (429). Pulando envio.")

            # Limpeza de Mídia
            if foto and os.path.exists(foto):
                await asyncio.sleep(1)
                try:
                    os.remove(foto)
                except:
                    pass

        except Exception as e:
            logger.error(f"⚠️ Erro no Worker: {e}")
        finally:
            fila_postagem.task_done()
            logger.info("⏳ Aguardando 3 minutos para a próxima...")
            await asyncio.sleep(180)  # Intervalo anti-flood (Obrigatório)


async def processar_oferta(texto_original: str, link_bruto: str, event):
    # 1. RESOLVE LINK E ANTI-REPETIÇÃO
    url_real = await link_router.resolver_link_real(link_bruto)
    if not url_real: return

    url_limpa = url_real.split('?')[0]
    if any(url_limpa in l for l in links_processados): return
    links_processados.append(url_limpa)
    if len(links_processados) > 200: links_processados.pop(0)

    # 2. ROTEAMENTO E FILTRO ML (CORRIGIDO)
    link_final, loja, _ = link_router.processar(url_real)

    # Bloqueio do Mercado Livre (Independente de como escreverem)
    if not loja or "MERCADO" in loja.upper():
        logger.warning(f"🚫 Bloqueado: {loja}")
        return

    logger.info(f"🔎 Captado: {loja}")

    # 3. LIMPEZA TOTAL DE LINKS DE TERCEIROS NO TEXTO
    texto_puro = re.sub(r'https?://\S+', '', texto_original).strip()

    # 4. DOWNLOAD DE MÍDIA
    caminho_foto = None
    try:
        if event.message.photo:
            caminho_foto = await event.message.download_media(file=f"oferta_{event.message.id}.jpg")
        elif loja == "AMAZON":
            caminho_foto = await baixar_imagem_amazon(link_final, f"oferta_{event.message.id}.jpg")
    except Exception as e:
        logger.warning(f"🖼️ Erro ao obter imagem: {e}")

    # 5. ENTRADA NA FILA (SEM IA AQUI)
    # A IA foi movida para o 'trabalhador_da_fila' para evitar o erro 429
    await fila_postagem.put((texto_puro, link_final, caminho_foto, loja))
    logger.info(f"📥 Adicionado à fila. Posição: {fila_postagem.qsize()}")


# --- EXECUÇÃO PRINCIPAL ---

async def main():
    await client.start()

    # Valida canais e inicia fila
    VALID_CANAIS = await resolve_safe_channels()
    asyncio.create_task(trabalhador_da_fila())

    @client.on(events.NewMessage(chats=VALID_CANAIS))
    async def handler(event):
        msg = event.message.message or ""
        urls = re.findall(r'(https?://\S+)', msg)
        for url in urls:
            await processar_oferta(msg, url, event)

    logger.success(f"🚀 Rodando em {len(VALID_CANAIS)} fontes.")
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass