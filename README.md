# Zabbia - Copiloto de Infraestrutura para Zabbix

Zabbia é um copiloto de infraestrutura com IA que se conecta ao Zabbix e transforma dados de monitoramento em interações em linguagem natural. O sistema permite consultas como "Quais hosts estão com CPU acima de 80%?", "Me mostre o uptime do host web01", entre outras.

## Requisitos

- Docker e Docker Compose
- Conexão com um servidor Zabbix 6.0+ para funcionalidades completas

## Estrutura do Projeto

```
zabbia/
├── backend/            # Código-fonte do backend
├── config/             # Arquivos de configuração
├── docker/             # Arquivos Dockerfile
├── frontend/           # Código-fonte do frontend
├── zabbia/             # Estrutura do módulo Python
│   └── backend/        # Código-fonte organizado
├── docker-compose.yml  # Configuração Docker Compose
├── main.py             # Ponto de entrada da aplicação
└── requirements.txt    # Dependências Python
```

## Funcionalidades Principais

- Geração de consultas SQL otimizadas para o banco de dados Zabbix
- Interpretação de logs e triggers em linguagem natural
- Resposta conversacional e contextual
- Criação automática de gráficos
- Resumo inteligente de alertas

## Configuração

1. Clone o repositório
2. Configure o arquivo `config/zabbia.json` com suas credenciais do Zabbix
3. Execute os contêineres Docker

## Execução

Para iniciar o projeto:

```bash
docker compose up
```

Os serviços ficarão disponíveis em:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Documentação API: http://localhost:8000/docs

## Desenvolvimento

### Backend

O backend é construído com:
- FastAPI
- SQLModel para acesso ao banco de dados
- WebSockets para comunicação em tempo real

### Frontend

O frontend é construído com:
- Next.js 14
- React 18
- Tailwind CSS
- Componentes shadcn/ui

## Comandos Úteis

| Comando | Descrição |
|---------|-----------|
| `/init` | Gera scaffold completo |
| `/sql <Q>` | Retorna apenas SQL para uma consulta |
| `/graph <Q>` | Retorna apenas JSON Schema para geração de gráfico |
| `/api <A>` | Retorna apenas payload da Zabbix API |

## Licenciamento

O sistema requer uma licença válida para uso em produção. O licenciamento é baseado em JWT, incluindo:
- Nome do cliente
- Data de expiração
- Número de usuários permitidos

## Status do Projeto

Versão atual: 0.1.0 (Desenvolvimento)

## Contribuição

Veja o arquivo CONTRIBUTING.md para informações sobre como contribuir para o projeto. 