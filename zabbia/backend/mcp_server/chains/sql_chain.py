import os
import aiohttp
from typing import Dict, Any
import re

class SQLGenerationChain:
    def __init__(self):
        self.openrouter_endpoint = "https://openrouter.ai/api/v1/chat/completions"
        self.default_model = "openai/gpt-4o-mini"
        
        # Carregar sistema de prompts
        self.system_prompt = """Você é um especialista em SQL para o banco de dados do Zabbix.
Sua tarefa é converter perguntas em linguagem natural para consultas SQL otimizadas que podem ser executadas diretamente no banco do Zabbix.

Siga estas diretrizes:
1. Gere apenas SQL válido para PostgreSQL/MySQL, respeitando a estrutura do Zabbix
2. Use JOINs apropriados e cláusulas WHERE para filtrar dados
3. Utilize subconsultas e CTEs quando necessário para consultas complexas
4. Adicione comentários explicativos para colunas ou joins complexos
5. Inclua limitações de tempo sempre que possível (ex: últimas 24h)
6. Use aliases de tabela para clareza (h para hosts, i para items, etc.)
7. Formate o SQL para legibilidade com indentação adequada

Principais tabelas do Zabbix:
- hosts - Armazena hosts monitorados (hostid, host, name, status)
- items - Métricas coletadas dos hosts (itemid, hostid, name, key_, value_type)
- history_* - Valores históricos (history, history_uint, etc.) com (itemid, clock, value)
- triggers - Condições de alerta (triggerid, description, expression)
- events - Eventos gerados por triggers (eventid, source, object, objectid, clock, value)
- problems - Problemas ativos (eventid, source, objectid, clock, name, severity)
- users - Usuários Zabbix (userid, alias, name, surname)
- graphs - Gráficos configurados (graphid, name, width, height)

Tipos de valores (value_type na tabela items):
0: float (history), 1: string (history_str), 2: log (history_log), 
3: integer (history_uint), 4: text (history_text)

Em sua resposta, forneça APENAS a consulta SQL sem nenhuma explicação. Utilize o dialeto SQL compatível com PostgreSQL.
"""
    
    async def run(self, query: str, api_key: str) -> str:
        """
        Executa a chain de geração de SQL com o OpenRouter.
        """
        # Preparar mensagens para o modelo
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query}
        ]
        
        # Fazer a chamada para o OpenRouter
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.default_model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1000
            }
            
            async with session.post(
                self.openrouter_endpoint,
                headers=headers,
                json=payload
            ) as response:
                response_data = await response.json()
                
                if "error" in response_data:
                    raise ValueError(f"Erro do OpenRouter: {response_data['error']}")
                
                # Extrair resposta
                sql_response = response_data["choices"][0]["message"]["content"]
                
                # Extrair SQL se estiver em um bloco de código
                sql_match = re.search(r"```sql\n(.*?)```", sql_response, re.DOTALL)
                if sql_match:
                    sql = sql_match.group(1).strip()
                else:
                    # Se não estiver em um bloco de código, usar a resposta completa
                    sql = sql_response.strip()
                
                return sql 