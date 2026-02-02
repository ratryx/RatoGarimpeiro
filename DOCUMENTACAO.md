# Rato Garimpeiro Enterprise - Documentacao Tecnica Completa

## Indice

1. [Visao Geral do Projeto](#1-visao-geral-do-projeto)
2. [Arquitetura e Estrutura de Pastas](#2-arquitetura-e-estrutura-de-pastas)
3. [Stack Tecnologica](#3-stack-tecnologica)
4. [Fluxo de Execucao](#4-fluxo-de-execucao)
5. [Detalhamento dos Modulos](#5-detalhamento-dos-modulos)
6. [Servicos Externos e Integracoes](#6-servicos-externos-e-integracoes)
7. [Configuracao e Variaveis de Ambiente](#7-configuracao-e-variaveis-de-ambiente)
8. [Deploy e CI/CD](#8-deploy-e-cicd)
9. [Tratamento de Erros e Resiliencia](#9-tratamento-de-erros-e-resiliencia)
10. [Solucao de Problemas](#10-solucao-de-problemas)
11. [Possiveis Melhorias](#11-possiveis-melhorias)

---

## 1. Visao Geral do Projeto

**Rato Garimpeiro** e um bot de automacao de marketing de afiliados. Ele monitora canais do Telegram em busca de ofertas de produtos, injeta links de afiliado (focado em Amazon), gera legendas de venda usando IA e distribui as ofertas para WhatsApp e Twitter/X.

**Resumo do fluxo:**

```
Telegram (30+ canais fonte)
    -> Detecta ofertas com URLs
    -> Identifica a loja e injeta tag de afiliado
    -> Gera legenda com IA (Gemini/Groq)
    -> Envia para WhatsApp (UAZAPI) e Twitter/X (Tweepy)
```

**Modelo de receita:** Comissoes de afiliado, principalmente Amazon Associates, com suporte a Awin (Nike, Adidas, LG, Puma, etc.) e Admitad (AliExpress, Shopee).

---

## 2. Arquitetura e Estrutura de Pastas

```
RatoGarimpeiro/
├── .github/workflows/
│   └── deploy.yml              # Pipeline CI/CD (GitHub Actions)
├── logs/                       # Logs da aplicacao (rotacao diaria, 7 dias)
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── constants.py        # Canais fonte, lojas ativas, IDs de merchants
│   │   └── settings.py         # Carregamento de .env com Pydantic
│   ├── core/
│   │   ├── __init__.py
│   │   ├── ai_brain.py         # Geracao de legendas com IA (Gemini + Groq)
│   │   ├── link_router.py      # Roteamento de links e injecao de tags de afiliado
│   │   └── amazon_image.py     # Scraping de imagens de produtos Amazon
│   └── infrastructure/
│       ├── __init__.py
│       └── whatsapp_client.py  # Cliente WhatsApp via UAZAPI
├── main.py                     # Ponto de entrada - orquestrador principal
├── espiao_wa.py                # Utilitario para entrar em grupos WhatsApp
├── limpar_fila.py              # Utilitario para limpar fila do UAZAPI
├── teste_ia.py                 # Script de teste da IA
├── verificar_modelos.py        # Verificacao de modelos Gemini disponiveis
├── requirements.txt            # Dependencias Python
├── .env                        # Credenciais e chaves de API (nao versionado)
└── sanguessuga_session.session # Sessao do Telegram (Telethon)
```

**Separacao de responsabilidades:**

- `src/config/` - Configuracao pura (constantes, variaveis de ambiente)
- `src/core/` - Logica de negocio (IA, roteamento de links, scraping de imagens)
- `src/infrastructure/` - Integracao com servicos externos (WhatsApp)
- `main.py` - Orquestracao: listener do Telegram, fila async, workers de envio

---

## 3. Stack Tecnologica

| Categoria | Tecnologia | Funcao |
|-----------|-----------|--------|
| Linguagem | Python 3.x | Toda a aplicacao |
| Telegram | Telethon | Monitoramento de canais |
| IA Primaria | Google Gemini (gemini-2.5-flash) | Geracao de legendas de venda |
| IA Backup | Groq (llama-3.3-70b-versatile) | Fallback se Gemini falhar |
| WhatsApp | UAZAPI (httpx async) | Envio de mensagens e imagens |
| Twitter | Tweepy (API v2) | Publicacao de tweets |
| Config | Pydantic Settings | Validacao tipada de .env |
| Logs | Loguru | Logging async com rotacao |
| Retry | Tenacity | Retentativas com backoff exponencial |
| Scraping | BeautifulSoup4 + httpx | Extracao de imagens Amazon |
| HTTP | httpx + aiohttp | Requisicoes async |
| Fuzzy Match | RapidFuzz | Comparacao de strings |
| Deploy | GitHub Actions + systemd | CI/CD automatizado |

---

## 4. Fluxo de Execucao

### 4.1. Inicializacao (`main.py`)

1. Carrega variaveis de ambiente via Pydantic (`settings.py`)
2. Inicializa o cliente Telegram (Telethon) com sessao persistente
3. Inicializa os clientes de IA (Gemini + Groq)
4. Inicializa o cliente WhatsApp (UAZAPI)
5. Inicializa o cliente Twitter/X (Tweepy)
6. Valida os canais do Telegram (filtra canais mortos/privados)
7. Inicia o worker da fila async

### 4.2. Monitoramento e Processamento

```
Nova mensagem no Telegram
    │
    ├─ Extrai URLs via regex
    ├─ Resolve URLs encurtadas (bit.ly, amzn.to, t.co)
    ├─ Verifica deduplicacao (ultimos 200 links em memoria)
    │
    ▼
LinkRouter (link_router.py)
    │
    ├─ Amazon? → Limpa tags concorrentes, injeta "ratogarimpeir-20"
    ├─ Nike/Adidas/LG/etc? → Gera link Awin com merchant ID
    ├─ AliExpress/Shopee? → Aplica prefixo Admitad
    ├─ Mercado Livre? → Bloqueado (ou modo manual)
    └─ Outro? → Descartado
    │
    ▼
Fila Async (asyncio.Queue)
    │  intervalo de 3 minutos entre envios
    │
    ▼
Worker de Envio
    ├─ Gera legenda com IA (Gemini → Groq → texto fallback)
    ├─ Envia WhatsApp: imagem + legenda (/send/media)
    │   └─ Fallback: texto com link preview (/send/text)
    └─ Publica no Twitter/X (se dentro do limite diario)
```

### 4.3. Rate Limiting

- **Fila de envio:** 1 oferta a cada 3 minutos
- **Twitter:** Maximo 15 posts/dia (configuravel via `LIMITE_DIARIO_X`)
- **Twitter 429:** Cooldown automatico de 30 minutos
- **Deduplicacao:** Lista circular de 200 links em memoria (FIFO)

---

## 5. Detalhamento dos Modulos

### 5.1. `main.py` - Orquestrador (~280 linhas)

Ponto de entrada da aplicacao. Responsabilidades:

- **Event handler do Telegram:** Escuta novas mensagens nos canais configurados
- **`processar_oferta()`:** Pipeline de processamento (resolver URLs, deduplicar, baixar midia, rotear link)
- **`fila_postagem`:** Fila async que desacopla a captura do envio
- **`trabalhador_da_fila()`:** Worker que consome a fila a cada 3 minutos
- **Envio para WhatsApp e Twitter:** Monta a mensagem final e despacha

Estado em memoria:
```python
links_processados = []       # Deduplicacao (max 200, FIFO)
posts_twitter_hoje = 0       # Contador diario de tweets
fila_postagem = asyncio.Queue()  # Buffer de ofertas
twitter_blocked_until = 0    # Timestamp de cooldown do Twitter
```

### 5.2. `src/core/ai_brain.py` - Motor de IA (~130 linhas)

Gera legendas de venda no estilo "vendedor agressivo". Cadeia de fallback:

1. **Gemini 2.5 Flash** (primario) - gratuito, rapido, safety settings desabilitados (`BLOCK_NONE`)
2. **Groq LLM** (backup) - llama-3.3-70b, inference rapida
3. **Texto hardcoded** (ultimo recurso) - "OFERTA IMPERDIVEL..."

Features:
- Prompt engineering para estilo "Rato Garimpeiro" (urgencia, emojis, CTA)
- Limpeza de markdown (remove `**`, `##`, etc.)
- Retry com tenacity (backoff exponencial)
- Totalmente async

### 5.3. `src/core/link_router.py` - Roteador de Links (~230 linhas)

Cerebro da monetizacao. Identifica a loja de origem e aplica a estrategia de afiliacao correta.

**Lojas suportadas:**

| Loja | Rede | Metodo |
|------|------|--------|
| Amazon (.com.br, .com, amzn.to, a.co) | Amazon Associates | Injecao de tag `?tag=ratogarimpeir-20` |
| Nike, Adidas, CEA, LG, Puma, Mizuno, Centauro, Olympikus, Stanley | Awin | DeepLink: `awin1.com/cread.php?awinmid=[ID]&awinaffid=[ID]&ue=[URL]` |
| AliExpress | Admitad | Prefixo: `rzekl.com/g/...?ulp=[URL]` |
| Shopee | Admitad | Prefixo: `xqjeo.com/g/...?ulp=[URL]` |

**Funcionalidades:**
- Resolucao de URLs encurtadas (segue redirects)
- Limpeza de tags de afiliado concorrentes em links Amazon
- Deteccao de loja por dominio e patterns de URL
- Controle via `LOJAS_ATIVAS` em `constants.py`

### 5.4. `src/core/amazon_image.py` - Scraper de Imagens (~70 linhas)

Extrai imagens HD de produtos Amazon:
- Faz parse do HTML da pagina do produto com BeautifulSoup
- Remove parametros de limitacao de tamanho da Amazon (`._AC_SY200_.jpg` → `.jpg`)
- Usa User-Agent aleatorio (fake-useragent) para evitar bloqueio
- Retorna imagem em alta resolucao para preview no WhatsApp

### 5.5. `src/infrastructure/whatsapp_client.py` - Cliente WhatsApp (~100 linhas)

Integra com a API UAZAPI para envio de mensagens:

- **`/send/media`** - Envia imagem (base64) + legenda
- **`/send/text`** - Envia texto com link preview (fallback)
- Simula delay de digitacao (1-2 segundos)
- Autenticacao via token no header
- Tratamento de erros HTTP (401 = token expirado)

### 5.6. `src/config/constants.py` - Painel de Controle (~80 linhas)

Centralizacao de configuracoes de negocio:

- **`LOJAS_ATIVAS`** - Liga/desliga lojas individualmente (`True`/`False`)
- **`CANAIS_FONTE`** - Lista de 30+ canais Telegram monitorados
- **`MEUS_CANAIS`** - Canais proprios de distribuicao (por nicho)
- **`ID_LOJA_*`** - IDs de merchants Awin para cada loja

### 5.7. `src/config/settings.py` - Configuracao (~40 linhas)

Carregamento tipado de variaveis de ambiente com Pydantic Settings:
- Validacao automatica na inicializacao
- Erro claro se alguma variavel obrigatoria estiver faltando
- Suporte a valores default

---

## 6. Servicos Externos e Integracoes

### 6.1. Telegram (Telethon)
- **Funcao:** Fonte de dados - monitora canais de promocao
- **Auth:** API_ID + API_HASH + sessao persistente
- **Canais:** 30+ canais configurados em `constants.py`

### 6.2. Google Gemini
- **Modelo:** gemini-2.5-flash (gratuito)
- **Funcao:** Geracao de legendas de venda
- **Safety:** Todos os filtros desabilitados (`BLOCK_NONE`)
- **Fallback:** Groq se quota excedida

### 6.3. Groq Cloud
- **Modelo:** llama-3.3-70b-versatile
- **Funcao:** Backup de IA se Gemini falhar
- **Vantagem:** Inference extremamente rapida

### 6.4. UAZAPI (WhatsApp)
- **Funcao:** Envio de ofertas para WhatsApp
- **Plano Free:** Token expira a cada 1 hora
- **Endpoints:** /send/media, /send/text, /group/join, /sender/clearall

### 6.5. Twitter/X (Tweepy)
- **API:** v2 com OAuth 1.0a
- **Limite:** 15 posts/dia (configuravel)
- **Cooldown:** 30 min automatico no erro 429

### 6.6. Redes de Afiliados
- **Amazon Associates:** Tag direta na URL
- **Awin:** DeepLink com merchant IDs (9 lojas)
- **Admitad:** Prefixo de redirect (AliExpress, Shopee)

---

## 7. Configuracao e Variaveis de Ambiente

### Arquivo `.env` (obrigatorio, nao versionado)

| Variavel | Descricao | Obrigatorio |
|----------|-----------|-------------|
| `API_ID` | ID da aplicacao Telegram | Sim |
| `API_HASH` | Hash da aplicacao Telegram | Sim |
| `PHONE_NUMBER` | Telefone do dono do bot | Sim |
| `ADMIN_USER` | Telegram ID do admin | Sim |
| `GROQ_API_KEY` | Chave API Groq | Sim |
| `GEMINI_API_KEY` | Chave API Google Gemini | Recomendado |
| `AMAZON_TAG` | Tag de afiliado Amazon | Sim |
| `AWIN_AFFILIATE_ID` | ID de afiliado Awin | Se usar Awin |
| `WA_INSTANCE_TOKEN` | Token UAZAPI | Sim |
| `WA_TARGET_NUMBER` | Numero/grupo destino WhatsApp | Sim |
| `WA_BASE_URL` | URL base da API UAZAPI | Sim |
| `X_API_KEY`, `X_API_SECRET` | Consumer keys Twitter | Se usar Twitter |
| `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` | Tokens de acesso Twitter | Se usar Twitter |
| `X_BEARER_TOKEN` | Bearer token Twitter | Se usar Twitter |
| `LIMITE_DIARIO_X` | Max tweets por dia (default: 15) | Nao |

### Arquivo `src/config/constants.py`

Para ativar/desativar lojas, altere `LOJAS_ATIVAS`:

```python
LOJAS_ATIVAS = {
    "AMAZON": True,          # Automacao completa
    "MERCADO_LIVRE": False,  # Modo manual
    "ALIEXPRESS": True,      # Via Admitad
    "SHOPEE": True,          # Via Admitad
    "AWIN_NIKE": True,       # Via Awin
    # ... demais lojas
}
```

---

## 8. Deploy e CI/CD

### Pipeline (`.github/workflows/deploy.yml`)

Acionado a cada push na branch `main`:

1. Conecta via SSH na VPS
2. Clona ou atualiza o repositorio
3. Cria/atualiza venv Python
4. Instala dependencias (`pip install -r requirements.txt`)
5. Reinicia o servico systemd (`bot-afiliados`)

### Servico systemd

O bot roda como servico Linux com restart automatico:
- **Servico:** `bot-afiliados`
- **Restart:** Automatico apos 30s em caso de crash
- **Logs:** `logs/sanguessuga.log` (rotacao diaria, retencao 7 dias)

### Secrets do GitHub necessarios

- `VPS_HOST` - IP/hostname da VPS
- `VPS_USER` - Usuario SSH
- `VPS_SSH_KEY` - Chave SSH privada
- `GH_TOKEN` - Token GitHub (se repo privado)

---

## 9. Tratamento de Erros e Resiliencia

| Cenario | Comportamento |
|---------|---------------|
| Crash do servico | systemd reinicia em 30s |
| Queda de rede | Telethon reconecta automaticamente |
| Rate limit Twitter (429) | Cooldown de 30 min, continua processando |
| Token UAZAPI expirado (401) | Notifica admin, requer renovacao manual |
| Gemini sem quota | Fallback automatico para Groq |
| Groq indisponivel | Fallback para texto hardcoded |
| Canal Telegram morto | Ignorado, bot continua com os demais |
| Falha ao baixar imagem | Envia texto sem imagem (fallback) |

**Armazenamento:** 100% em memoria (sem banco de dados). Restart limpa o historico de deduplicacao - trade-off aceito pela simplicidade.

---

## 10. Solucao de Problemas

### Token UAZAPI expirado
- **Sintoma:** `Falha ao enviar WhatsApp (401): Invalid token`
- **Solucao:** Criar nova instancia no UAZAPI e atualizar `WA_INSTANCE_TOKEN` no `.env`

### IA nao gera legenda
- **Sintoma:** `Legenda da IA falhou, abortando postagem`
- **Solucao:** Verificar chaves GROQ_API_KEY e GEMINI_API_KEY. O sistema usa fallback automatico.

### Canal Telegram invalido
- **Sintoma:** `Canal invalido ou nao existente: @canal -> IGNORADO`
- **Solucao:** Remover o canal de `CANAIS_FONTE` em `constants.py`

### Bot nao envia tweets
- **Sintoma:** Ofertas no WhatsApp mas nao no Twitter
- **Solucao:** Verificar se `posts_twitter_hoje` atingiu `LIMITE_DIARIO_X`. Verificar credenciais Twitter no `.env`.

---

## 11. Possiveis Melhorias

### Alta Prioridade

**1. Persistencia de dados com banco de dados leve**
- **Problema atual:** Deduplicacao em memoria (lista de 200 links) e perdida ao reiniciar, causando repostagem de ofertas duplicadas.
- **Sugestao:** Usar SQLite ou Redis para persistir links processados, estatisticas de envio e historico de ofertas.
- **Beneficio:** Elimina duplicatas pos-restart e permite gerar relatorios de performance.

**2. Renovacao automatica do token UAZAPI**
- **Problema atual:** O token do plano free expira a cada hora, exigindo intervencao manual.
- **Sugestao:** Implementar rotina automatica que renova o token via API do UAZAPI antes da expiracao, ou migrar para plano pago com token persistente.
- **Beneficio:** Operacao 24/7 sem intervencao humana.

**3. Dashboard de monitoramento**
- **Problema atual:** Monitoramento apenas via logs em arquivo. Sem visibilidade em tempo real do status do bot.
- **Sugestao:** Criar um painel web simples (FastAPI + HTMX ou Streamlit) mostrando: ofertas processadas, taxa de envio, erros, status dos servicos, fila pendente.
- **Beneficio:** Visibilidade operacional sem precisar acessar a VPS.

### Media Prioridade

**4. Sistema de categorias e canais de distribuicao**
- **Problema atual:** Os canais proprios do Telegram (`MEUS_CANAIS`) estao definidos mas nao sao utilizados ativamente para distribuicao categorizada.
- **Sugestao:** Classificar ofertas por categoria (tech, casa, fitness, etc.) usando a IA e distribuir para os canais tematicos correspondentes.
- **Beneficio:** Publico mais segmentado, maior taxa de conversao.

**5. Fila persistente**
- **Problema atual:** A `asyncio.Queue` e in-memory. Se o bot reiniciar com ofertas na fila, elas sao perdidas.
- **Sugestao:** Usar uma fila persistente (Redis Queue, ou mesmo SQLite como fila). Ao reiniciar, o bot retoma de onde parou.
- **Beneficio:** Zero perda de ofertas durante deploys ou restarts.

**6. Metricas e analytics de conversao**
- **Problema atual:** Nenhum rastreamento de quais ofertas geram cliques ou vendas.
- **Sugestao:** Integrar com a API de relatorios da Amazon Associates e Awin para rastrear conversoes. Armazenar metricas localmente e exibir no dashboard.
- **Beneficio:** Identificar quais tipos de ofertas, lojas e horarios geram mais receita.

**7. Testes automatizados**
- **Problema atual:** Apenas scripts de teste manuais (`teste_ia.py`, `verificar_modelos.py`). Sem suite de testes.
- **Sugestao:** Adicionar testes unitarios (pytest) para `link_router.py` (critico - lida com dinheiro), `ai_brain.py`, e testes de integracao para o fluxo completo.
- **Beneficio:** Seguranca para refatorar e adicionar features sem quebrar a monetizacao.

### Baixa Prioridade (Futuro)

**8. Suporte a multiplos grupos WhatsApp**
- **Problema atual:** Envio para um unico grupo/numero.
- **Sugestao:** Configurar multiplos destinos WhatsApp por categoria de produto, similar aos canais Telegram tematicos.
- **Beneficio:** Distribuicao mais ampla e segmentada.

**9. Filtragem inteligente de ofertas**
- **Problema atual:** Toda oferta Amazon e processada independente da qualidade.
- **Sugestao:** Usar a IA para avaliar a qualidade da oferta (desconto real, preco historico, relevancia) antes de postar. Descartar ofertas fracas.
- **Beneficio:** Maior credibilidade do canal e melhor taxa de conversao.

**10. Migracao para container Docker**
- **Problema atual:** Deploy depende de venv e systemd configurados manualmente na VPS.
- **Sugestao:** Criar Dockerfile + docker-compose. O CI/CD faria build da imagem e restart do container.
- **Beneficio:** Deploy reprodutivel, isolamento de ambiente, facilita migracao de servidor.

**11. Sistema de notificacao de saude**
- **Problema atual:** Falhas silenciosas (ex: bot parou de receber mensagens do Telegram sem erro explicito).
- **Sugestao:** Heartbeat periodico que envia status para o admin via WhatsApp/Telegram. Se o heartbeat parar, alerta automatico.
- **Beneficio:** Deteccao proativa de problemas antes de impactar a receita.

**12. Rate limiting adaptativo**
- **Problema atual:** Intervalo fixo de 3 minutos entre envios, independente do volume.
- **Sugestao:** Ajustar dinamicamente o intervalo baseado no horario (mais frequente em horarios de pico de compras, menos a noite).
- **Beneficio:** Maximizar o volume de ofertas nos horarios de maior conversao.
