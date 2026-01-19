import httpx
import asyncio
from src.config.settings import config


async def resetar_servidor_uazapi():
    token = config.WA_INSTANCE_TOKEN
    base_url = config.WA_BASE_URL
    headers = {"token": token}

    # Endpoint correto conforme sua documentação de envio em massa
    endpoint = f"{base_url}/sender/clearall"

    print(f"🧹 Limpando fila via DELETE em: {endpoint}")

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.delete(endpoint, headers=headers)
            if response.status_code == 200:
                print("✅ SUCESSO: Todas as mensagens removidas do servidor!")
            else:
                print(f"❌ Erro na API ({response.status_code}): {response.text}")
        except Exception as e:
            print(f"❌ Falha: {e}")


if __name__ == "__main__":
    asyncio.run(resetar_servidor_uazapi())