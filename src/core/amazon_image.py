import httpx
import os
import re
from bs4 import BeautifulSoup
from loguru import logger


async def baixar_imagem_amazon(url: str, nome_arquivo: str) -> str | None:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
    }

    try:
        async with httpx.AsyncClient(timeout=20, headers=headers, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None

            html = resp.text

        soup = BeautifulSoup(html, "html.parser")

        # Tenta pegar a imagem principal do produto (mais nítida que o og:image)
        img_tag = soup.find("img", {"id": "landingImage"}) or soup.find("meta", property="og:image")

        if not img_tag:
            logger.warning("❌ Amazon: Não foi possível localizar a imagem do produto")
            return None

        # Extrai a URL (do atributo 'src', 'data-old-hires' ou 'content')
        img_url = img_tag.get("data-old-hires") or img_tag.get("src") or img_tag.get("content")

        if not img_url:
            return None

        # --- TRUQUE PARA ALTA RESOLUÇÃO ---
        # A Amazon coloca códigos de redimensionamento na URL, ex: ._AC_SY200_.jpg
        # Removemos o trecho entre os dois pontos para pegar a imagem original (4k/HD)
        img_url_hd = re.sub(r'\._AC_.*_\.', '.', img_url)

        logger.info(f"📸 Baixando imagem HD: {img_url_hd}")

        async with httpx.AsyncClient(timeout=20) as client:
            img_resp = await client.get(img_url_hd)

            if img_resp.status_code == 200:
                with open(nome_arquivo, "wb") as f:
                    f.write(img_resp.content)

                # Verifica se o arquivo não está vazio ou corrompido
                if os.path.getsize(nome_arquivo) > 1000:
                    logger.success("🖼️ Imagem Amazon HD capturada!")
                    return nome_arquivo

        return None

    except Exception as e:
        logger.error(f"⚠️ Erro ao processar imagem Amazon: {e}")
        return None