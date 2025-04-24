# 🚀 Zabbia

Zabbia é um copiloto conversacional de infraestrutura que integra IA com Zabbix para transformar dados de monitoramento em interações em linguagem natural.

## 🌟 Recursos

- **Chat conversacional** - Pergunte sobre hosts, métricas e alertas em linguagem natural
- **Geração de SQL** - Converte perguntas em consultas SQL otimizadas para o banco Zabbix
- **Chamadas API JSON-RPC** - Gera payloads para a API do Zabbix automaticamente
- **Visualização de dados** - Cria gráficos dinâmicos a partir de comandos de texto
- **Análise preventiva** - Recomendações baseadas em tendências de métricas

## 🛠️ Tecnologias

| Camada     | Stack                                                       |
|------------|-------------------------------------------------------------|
| Frontend   | Next.js 15, TypeScript, TailwindCSS, shadcn/ui, React Query |
| Charts     | Recharts                                                    |
| Auth       | NextAuth.js (JWT)                                           |
| Backend    | FastAPI, SQLModel, pydantic v2, uvicorn                     |
| IA/MCP     | LangChain, OpenRouter (meta-llama/llama-4-maverick:free), Python                 |
| DB         | PostgreSQL 16 (schema Zabbix 6)                             |
| DevOps     | Docker, Docker Compose, GitHub Actions                      |

## 🚀 Instruções de Uso

### Pré-requisitos

- Docker e Docker Compose
- Um servidor Zabbix 6.0+ acessível
- Chave de API do OpenRouter (para funcionalidades de IA)

### Iniciando com Docker

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/zabbia.git
cd zabbia
```

2. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais
```

3. Inicie a aplicação:
```bash
docker compose up -d
```

4. Acesse a aplicação:
- Frontend: http://localhost:3000
- API: http://localhost:8000/docs

### Comandos especiais de chat

- `/generate-sql <pergunta>` - Gera SQL para consultar banco do Zabbix
- `/call-api <ação>` - Gera payload JSON-RPC para API Zabbix
- `/graph <pergunta>` - Gera um gráfico a partir da pergunta
- `/recommend <contexto>` - Fornece recomendações baseadas no contexto

## 📋 Estrutura do Projeto

```
zabbia/
├─ backend/
│  ├─ app/
│  │  ├─ api/routers/  # Endpoints FastAPI
│  │  ├─ domain/       # Modelos de domínio
│  │  ├─ services/     # Serviços de negócio
│  │  └─ main.py       # Ponto de entrada FastAPI
│  ├─ mcp_server/      # Servidor MCP (Machine Copilot)
│  │  ├─ chains/       # Chains LangChain 
│  │  └─ server.py     # gRPC wrapper
│  └─ tests/           # Testes unitários e de integração
├─ frontend/           # Next.js 15 (App Router)
│  ├─ app/
│  ├─ components/
│  └─ lib/
└─ docker-compose.yml  # Configuração de containers
```

## 🔒 Sistema de Licenciamento

O Zabbia implementa um sistema de licenciamento baseado em JWT:

1. Cada licença contém: cliente, data de expiração e número de seats
2. A verificação de licença é feita via middleware em todas as requisições
3. Licenses são geradas via CLI específico (consulte documentação)

## 🧪 Testes

Execute os testes com os seguintes comandos:

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## 📜 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, leia nosso guia de contribuição antes de enviar um pull request. 