import httpx
import asyncio


async def forcar_entrada_e_pegar_id():
    token = "88fe00c0-c342-4913-b0e8-52e48bd1d6ff"
    base_url = "https://bot-test.uazapi.com"
    link_grupo = "https://chat.whatsapp.com/J8fAB7GUChb2dl7Qo3uynL"

    headers = {
        "token": token,
        "Content-Type": "application/json"
    }

    endpoint = f"{base_url}/group/join"
    payload = {"invitecode": link_grupo}

    print(f"🚀 Enviando solicitação para: {endpoint}")

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(endpoint, headers=headers, json=payload)

            print(f"📡 Status da Resposta: {response.status_code}")

            # Tenta ler como JSON, se falhar, lê como texto bruto
            try:
                dados = response.json()
                print(f"📦 Resposta JSON: {dados}")

                # Procura o ID em diferentes lugares possíveis
                jid = None
                if isinstance(dados, dict):
                    jid = dados.get('id') or dados.get('response', {}).get('id')

                if jid:
                    print(f"\n🎯 ID ENCONTRADO: {jid}")
            except:
                print(f"📄 Resposta Texto: {response.text}")
                # Se o ID estiver no meio do texto, você conseguirá ver aqui

        except Exception as e:
            print(f"❌ Erro de conexão ou execução: {e}")


if __name__ == "__main__":
    asyncio.run(forcar_entrada_e_pegar_id())