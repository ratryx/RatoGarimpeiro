# 📖 RATO GARIMPEIRO ENTERPRISE: Manual de Operação e Estratégia de Foco Amazon

Este documento é o manual definitivo para operar o sistema Rato Garimpeiro. Ele foi otimizado para o modo **"Foco Total na Amazon"**, garantindo a máxima eficiência e lucro imediato.

---

## 1. 🥇 O Objetivo e o Fluxo de Lucro

Seu bot é uma máquina de garimpo de ofertas de afiliados. A estratégia é **descartar o que não é lucro fácil** e focar no volume da Amazon.

### 🎯 O Fluxo de Conversão

1.  **Mineração (Telegram):** O bot escuta os canais fontes mais ativos e nichados.
2.  **Filtro Rígido (Amazon-Only):** Qualquer link que não seja da Amazon é descartado imediatamente, garantindo que o tempo de processamento seja 100% dedicado ao seu parceiro principal.
3.  **Injeção de Comissão:** Sua tag de afiliado (`ratogarimpeir-20`) é inserida no link do produto Amazon.
4.  **Criação da Copy (IA):** O motor de IA (Groq ou Gemini) gera a legenda de impacto no estilo "Rato Garimpeiro".
5.  **Validação e Distribuição (WhatsApp):** A oferta é enviada para o seu número de WhatsApp (`5512992277250`) para sua revisão final, com a imagem do produto inclusa, aumentando a conversão.

---

## 2. ⚙️ Configuração, Instalação e Chaves

### 2.1. Instalação e Preparação

1.  **Crie a Estrutura de Pastas** conforme a arquitetura modular: `src/config/`, `src/core/`, `src/infrastructure/`.
2.  **Crie o Ambiente Virtual (`.venv`):**
    ```bash
    python -m venv .venv
    ```
3.  **Ative o Ambiente e Instale as Dependências:**
    ```bash
    .\venv\Scripts\activate
    pip install -r requirements.txt
    ```

### 2.2. O Arquivo de Chaves (`.env`)

Este arquivo na pasta raiz carrega todas as credenciais do sistema.

| Variável | Descrição | Status |
| :--- | :--- | :--- |
| `API_ID`, `API_HASH` | Acesso à sua conta do Telegram (Telethon). | **Obrigatório** |
| `GROQ_API_KEY` | Motor Primário de IA (velocidade máxima). | **Obrigatório** |
| `GEMINI_API_KEY` | Backup da IA (crucial se a Groq falhar). | **Recomendado** |
| `AMAZON_TAG` | **Sua Tag de Afiliado Amazon** (`ratogarimpeir-20`). | **Obrigatório** (Se não estiver aqui, você não ganha comissão). |
| `WA_INSTANCE_TOKEN` | Token da sua instância UAZAPI para envio de mensagens. | **Obrigatório** (Dura 1 hora no plano Free) |
| `LIMITE_DIARIO_X` | Limite máximo de posts no Twitter por dia (atualmente: 15). | Controle de Distribuição |

---

## 3. ⚔️ Chaveamento Rápido de Lojas (O Mestre)

Se em algum momento você quiser ativar outras lojas (por exemplo, Nike via Awin ou Mercado Livre, que exige postagem manual), você não precisa tocar em nenhum código de lógica.

A chave está no arquivo **`src/config/constants.py`**:

#### Como Mudar o Foco:

1.  Abra o arquivo **`src/config/constants.py`**.
2.  Localize o dicionário `LOJAS_ATIVAS`.
3.  Mude o valor de `False` para `True` na loja desejada e **reinicie o bot** com `python main.py`.

| Loja | Chave de Controle | Ação do Bot se Ativado (`True`) |
| :--- | :--- | :--- |
| **AMAZON** | `"AMAZON"` | **Automação 100%:** Insere afiliação e envia para o WhatsApp/X. |
| **MERCADO LIVRE** | `"MERCADO_LIVRE"` | **Modo Manual:** Envia o link e a legenda para o seu privado (`ADMIN_USER`) para você postar à mão. |
| **ADMITAD/AWIN** | Ex: `"AWIN_NIKE"` | O `link_router.py` tentará aplicar o prefixo/ID de afiliado. |

---

## 4. 🛑 Solução de Problemas e Erros Comuns

O bot foi construído para ser robusto, mas há três falhas externas que você deve monitorar:

### A. Token Expirado (UAZAPI)

| Sintoma | Causa | Solução |
| :--- | :--- | :--- |
| `❌ Falha ao enviar WhatsApp (401): Invalid token.` | Sua instância UAZAPI expirou (após 1 hora). O token (`WA_INSTANCE_TOKEN`) não é mais válido. | Crie uma **nova instância** e **substitua o token** no seu arquivo `.env` imediatamente. |

### B. Falha na Geração de Copy (IA)

| Sintoma | Causa | Solução |
| :--- | :--- | :--- |
| `WARNING | Legenda da IA falhou, abortando postagem` | Falha de conexão com Groq e Gemini. | Verifique o status das suas chaves Groq/Gemini. O sistema usará um "Fallback Manual". |

### C. Canais Mortos

| Sintoma | Causa | Solução |
| :--- | :--- | :--- |
| `❌ Canal inválido ou não existente: @ofertasparacasa -> IGNORADO.` | O canal fonte mudou de nome, foi deletado, ou ficou privado. | O bot continua rodando, mas você pode **remover o `@username`** do arquivo `src/config/constants.py` para limpar o log. |

---

## 5. ▶️ Como Iniciar a Mineração

Com todos os arquivos salvos e o `.venv` ativo, use o comando:

```bash
python main.py