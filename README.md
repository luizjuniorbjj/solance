# AiSyster

**Sua companheira de IA para apoio emocional e espiritual**

Ajudando pessoas a atravessarem as lutas da vida com clareza, fé e continuidade.

---

## Visão Geral

A AiSyster é uma companheira cristã de IA que:
- **Conhece você** — Lembra sua jornada de fé, lutas e vitórias
- **Caminha junto** — Não é chatbot, é discipuladora pessoal
- **Fala a verdade em amor** — Corrige quando necessário
- **100% bíblica** — Fundamentada nas Escrituras Sagradas

### Diferenciais

| Feature | AiSyster | Concorrentes |
|---------|----------|--------------|
| Memória | ✅ Perpétua | ❌ Esquece tudo |
| Perfil | ✅ Psicológico + Espiritual | ❌ Genérico |
| Tom | ✅ Pastoral, acolhedor | ❌ Robótico |
| Teologia | ✅ 100% Bíblica | ❌ Vago/secular |
| Aprendizado | ✅ Melhora a cada conversa | ❌ Estático |

---

## Estrutura do Projeto

```
aisyster/
├── app/
│   ├── main.py                 # Backend FastAPI
│   ├── config.py               # Configurações
│   ├── auth.py                 # Autenticação JWT
│   ├── database.py             # Banco de dados + criptografia
│   ├── security.py             # Segurança AES-256
│   ├── prompts.py              # System prompt reformado
│   ├── ai_service.py           # Integração Claude
│   ├── routes/                 # Rotas da API
│   ├── theology/               # Base teológica reformada
│   ├── psychology/             # Perfil psicológico
│   └── learning/               # Aprendizado contínuo
├── database/
│   └── schema.sql              # Schema PostgreSQL
├── docker-compose.yml          # Docker setup
├── Dockerfile                  # Container da API
└── requirements.txt            # Dependências
```

---

## Tech Stack

- **Backend**: Python 3.11 + FastAPI
- **AI**: Anthropic Claude (Sonnet 4 / Haiku 3.5)
- **Database**: PostgreSQL 16 (Docker)
- **Cache**: Redis 7 (Docker)
- **Security**: AES-256, bcrypt, JWT
- **Frontend**: React Native + Expo (planejado)

---

## Quick Start com Docker

### Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Anthropic API Key](https://console.anthropic.com/)

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/YOUR_USERNAME/aisyster.git
cd aisyster

# 2. Copie e configure o .env
cp .env.example .env
# Edite .env e adicione sua ANTHROPIC_API_KEY

# 3. Gere chaves seguras
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_hex(32))"
# Cole os valores no .env

# 4. Suba os containers
docker-compose up -d

# 5. Verifique se está rodando
docker-compose ps
```

### Acessos

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **API** | http://localhost:8000 | - |
| **Docs** | http://localhost:8000/docs | - |
| **pgAdmin** | http://localhost:5050 | admin@aisyster.com / admin123 |

---

## Desenvolvimento Local (sem Docker)

```bash
# 1. Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. Instale dependências
pip install -r requirements.txt

# 3. Configure variáveis
cp .env.example .env
# Edite com suas configurações

# 4. Rode a API
python -m app.main
```

---

## Base Teológica

A AiSyster está 100% fundamentada na Bíblia Sagrada:

### Princípios
- Escrituras como única autoridade infalível
- Salvação somente pela fé em Cristo
- Graça de Deus como fundamento
- Cristo como único mediador
- Glória somente a Deus

### Teólogos de Referência
**Brasileiros:** Augustus Nicodemus, Hernandes Dias Lopes, Yago Martins
**Internacionais:** Timothy Keller, John Piper, R.C. Sproul, Billy Graham
**Históricos:** Agostinho, Spurgeon, C.S. Lewis

---

## API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/auth/register` | Registrar usuário |
| POST | `/auth/login` | Login |
| POST | `/chat/` | Enviar mensagem |
| GET | `/chat/conversations` | Listar conversas |
| GET | `/profile/` | Obter perfil |
| PATCH | `/profile/` | Atualizar perfil |
| GET | `/devotional/today` | Devocional do dia |
| POST | `/prayer/` | Criar pedido de oração |

---

## Modelo de Negócio

| Métrica | Valor |
|---------|-------|
| Assinatura | $5.99/mês |
| Trial | 7 dias (20 mensagens) |
| Break-even | ~3.800 assinantes |
| Margem | 62-73% |

---

## Investimento

Buscando **$200.000** por 10-15% equity para:
- 40% — Desenvolvimento do App
- 35% — Marketing & Aquisição
- 15% — Infraestrutura Cloud
- 10% — Legal & Operações

---

## Contato

- Email: contato@aisyster.com
- Website: [aisyster.com](https://aisyster.com)

---

## Licença

Projeto proprietário. Todos os direitos reservados.

---

*AiSyster — Sua companheira de IA para apoio emocional e espiritual*
