import httpx
import base64
import os
from loguru import logger
from src.config.settings import config


class WhatsAppClient:
    def __init__(self):
        self.headers = {
            "token": config.WA_INSTANCE_TOKEN,
            "Content-Type": "application/json"
        }
        self.base_url = config.WA_BASE_URL
        self.target_number = config.WA_TARGET_NUMBER

    async def enviar_oferta(self, legenda: str, link_final: str, file_path: str = None):
        # Limpeza do número conforme a doc (apenas dígitos ou ID de grupo)
        destinatario = self.target_number.replace('"', '').replace("'", "").strip()

        # O campo 'text' serve como legenda no /send/media
        texto_completo = f"{legenda}\n\n🔗 {link_final}"

        b64_image = None

        # 1. PREPARAÇÃO DA IMAGEM (Base64)
        # A doc diz: "Suporta URLs ou arquivos base64"
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, "rb") as image_file:
                    b64_raw = base64.b64encode(image_file.read()).decode('utf-8')
                    # Formata cabeçalho para aceitação da API se necessário, mas raw costuma funcionar
                    b64_image = f"data:image/jpeg;base64,{b64_raw}"
            except Exception as e:
                logger.error(f"⚠️ Erro ao converter imagem para Base64: {e}")

        # 2. TENTATIVA PRINCIPAL: /send/media (Imagem Grande)
        if b64_image:
            try:
                endpoint = f"{self.base_url}/send/media"
                payload = {
                    "number": destinatario,
                    "type": "image",  # Obrigatório
                    "file": b64_image,  # A imagem em Base64
                    "text": texto_completo,  # Legenda da foto
                    "delay": 1200  # Simula digitação
                }

                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(endpoint, headers=self.headers, json=payload)

                    if response.status_code == 200:
                        logger.success(f"✅ Mídia enviada (/send/media) para {destinatario}")
                        return True, 200
                    else:
                        logger.warning(f"⚠️ Falha Mídia ({response.status_code}): {response.text}")
            except Exception as e:
                logger.error(f"⚠️ Erro de conexão no envio de mídia: {e}")

        # 3. FALLBACK INTELIGENTE: /send/text com PREVIEW HD
        # Se a mídia falhar (ou não existir), usamos o recurso 'Preview Personalizado' da doc
        try:
            endpoint_txt = f"{self.base_url}/send/text"

            payload = {
                "number": destinatario,
                "text": texto_completo,
                "delay": 1000,
                "linkPreview": True,  # Ativa o preview
                "linkPreviewLarge": True  # FORÇA O PREVIEW GRANDE
            }

            # Se temos a imagem em Base64, forçamos ela no preview do link!
            # Isso garante que mesmo sendo texto, a imagem apareça e não fique borrada
            if b64_image:
                payload["linkPreviewImage"] = b64_image

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(endpoint_txt, headers=self.headers, json=payload)

                if response.status_code == 200:
                    tipo = "com Preview HD" if b64_image else "Simples"
                    logger.success(f"📱 Texto {tipo} enviado para {destinatario}")
                    return True, 200
                else:
                    logger.error(f"❌ Erro UAZAPI ({response.status_code}): {response.text}")
                    return False, response.status_code

        except Exception as e:
            logger.error(f"❌ Erro crítico WA: {e}")
            return False, 500


whatsapp_client = WhatsAppClient()