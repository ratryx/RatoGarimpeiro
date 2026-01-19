from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, quote
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
from src.config.settings import config
from src.config.constants import (
    ID_LOJA_NIKE, ID_LOJA_CENTAURO, ID_LOJA_ADIDAS,
    ID_LOJA_CEA, ID_LOJA_OLYMPIKUS, ID_LOJA_LG,
    ID_LOJA_STANLEY, ID_LOJA_PUMA, ID_LOJA_MIZUNO
)


class LinkRouter:

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    async def resolver_link_real(self, url_curta: str) -> str:
        """Desenrola links encurtados (bit.ly, t.co, amzn.to, a.co) mantendo headers de mobile"""
        # Headers de iPhone para passar despercebido pelos sistemas anti-bot
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers=headers, verify=False) as client:
            try:
                resp = await client.get(url_curta)
                return str(resp.url)
            except Exception as e:
                logger.warning(f"⚠️ Erro ao resolver link {url_curta}: {e}")
                # Se der erro, retorna o link original pra tentar salvar na lógica abaixo
                return url_curta

    def _gerar_awin(self, url_real: str, merchant_id: str):
        """Gera link Awin padronizado usando seu ID: 2691470"""
        encoded = quote(url_real)
        # O parâmetro ue= define a URL de destino final no DeepLink da Awin
        return f"https://www.awin1.com/cread.php?awinmid={merchant_id}&awinaffid={config.AWIN_AFFILIATE_ID}&ue={encoded}&p={encoded}"

    def processar(self, url_real: str):
        """Cérebro de roteamento: Identifica a loja e aplica a sua tag de afiliado"""
        # Normaliza para minúsculo para facilitar a busca
        url_limpa = url_real.split('?')[0].lower()

        # --- 1. AMAZON (Radar Turbo - Lógica Original Preservada) ---
        # Lista de domínios possíveis da Amazon capturados pelo scraper
        DOMINIOS_AMAZON = [
            "amazon.com", "amazon.com.br", "amzn.to", "a.co",
            "smile.amazon.com", "m.media-amazon.com"
        ]

        if any(dom in url_limpa for dom in DOMINIOS_AMAZON):
            try:
                parsed = urlparse(url_real)
                qs = parse_qs(parsed.query)

                # Faxina nos parâmetros: Tira tags de outros afiliados para garantir sua comissão
                for bad in ['tag', 'ascsubtag', 'associate-id', 'utm_source', 'utm_medium', 'ref', 'ref_']:
                    qs.pop(bad, None)

                # Carimba com a SUA tag configurada no arquivo .env
                if config.AMAZON_TAG:
                    qs['tag'] = [config.AMAZON_TAG]

                nova_query = urlencode(qs, doseq=True)
                final = urlunparse(parsed._replace(query=nova_query))
                return final, "AMAZON", False
            except Exception as e:
                logger.error(f"Erro ao processar link Amazon: {e}")
                # Se falhar a limpeza, manda o link original mesmo
                return url_real, "AMAZON", False

        # --- 2. AWIN (Nike, Adidas, Stanley, LG, Puma, Mizuno, etc.) ---
        # Só processa se o AWIN_AFFILIATE_ID estiver configurado como 2691470
        if config.AWIN_AFFILIATE_ID:
            if "nike.com.br" in url_limpa:
                return self._gerar_awin(url_real, ID_LOJA_NIKE), "NIKE", False

            if "centauro.com.br" in url_limpa:
                return self._gerar_awin(url_real, ID_LOJA_CENTAURO), "CENTAURO", False

            if "adidas.com.br" in url_limpa:
                return self._gerar_awin(url_real, ID_LOJA_ADIDAS), "ADIDAS", False

            if "cea.com.br" in url_limpa:
                return self._gerar_awin(url_real, ID_LOJA_CEA), "CEA", False

            if "olympikus.com.br" in url_limpa:
                return self._gerar_awin(url_real, ID_LOJA_OLYMPIKUS), "OLYMPIKUS", False

            if "lg.com" in url_limpa:
                return self._gerar_awin(url_real, ID_LOJA_LG), "LG", False

            if "stanley-pmi.com.br" in url_limpa:
                return self._gerar_awin(url_real, ID_LOJA_STANLEY), "STANLEY", False

            if "puma.com.br" in url_limpa:
                return self._gerar_awin(url_real, ID_LOJA_PUMA), "PUMA", False

            if "mizuno.com.br" in url_limpa:
                return self._gerar_awin(url_real, ID_LOJA_MIZUNO), "MIZUNO", False

        # --- 3. ADMITAD (Shopee/AliExpress com seus links reais enviados) ---
        if "aliexpress.com" in url_limpa:
            # Link AliExpress Admitad configurado com parâmetro ?ulp=
            return f"https://rzekl.com/g/1e8d114494b08e05732d16525dc3e8/?ulp={quote(url_real)}", "ALIEXPRESS", False

        if "shopee.com.br" in url_limpa or "shope.ee" in url_limpa:
            # Link Shopee Admitad configurado com parâmetro ?ulp=
            return f"https://xqjeo.com/g/knlhlz71uxb08e05732d04f147125c/?ulp={quote(url_real)}", "SHOPEE", False

        if "shein.com" in url_limpa:
            return url_real, "SHEIN", True

        # --- 4. MANUAIS (O Resto - Lógica Original Preservada) ---
        if "mercadolivre.com" in url_limpa or "mercado.li" in url_limpa:
            return url_real, "MERCADO LIVRE", True

        if "magalu" in url_limpa or "magazineluiza" in url_limpa:
            return url_real, "MAGALU", True

        if "netshoes.com.br" in url_limpa:
            return url_real, "NETSHOES", True

        # Se não cair em nenhuma loja conhecida, retorna None para o main ignorar
        return None, None, None