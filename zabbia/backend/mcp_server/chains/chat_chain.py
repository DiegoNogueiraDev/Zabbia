import os
import json
import aiohttp
from typing import List, Dict, Any
import re

class ChatChain:
    def __init__(self):
        self.openrouter_endpoint = "https://openrouter.ai/api/v1/chat/completions"
        self.default_model = "openai/gpt-4o-mini"
        
        # Carregar sistema de prompts
        self.system_prompt = """Você é Zabbia, um copiloto de infraestrutura especializado em monitoramento Zabbix.

Como assistente técnico, você deve:
1. Responder dúvidas sobre hosts, recursos, métricas e alertas
2. Interpretar logs e eventos do Zabbix
3. Converter perguntas em linguagem natural para SQL otimizado para consultas no banco Zabbix
4. Gerar chamadas para API JSON-RPC do Zabbix
5. Ajudar a criar visualizações e dashboards
6. Oferecer sugestões preventivas com base em tendências de dados

Quando necessário, você pode identificar comandos especiais:
- /generate-sql <pergunta> - para gerar SQL otimizado
- /call-api <ação> - para gerar JSON-RPC
- /graph <pergunta> - para gerar dados de gráficos
- /recommend <contexto> - para receber sugestões preventivas

Use Markdown para formatação e tabelas. Seja técnico, direto e preciso.

Principais tabelas do Zabbix:
- hosts - Armazena hosts monitorados
- items - Métricas coletadas dos hosts
- history_* - Valores históricos (history, history_uint, etc.)
- triggers - Condições de alerta
- events - Eventos gerados por triggers
- problems - Problemas ativos
- users - Usuários Zabbix
- graphs - Gráficos configurados

Responda sempre em Português. Use termos técnicos quando apropriado.
"""
    
    async def run(self, messages: List[Dict[str, Any]], api_key: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executa a chain de chat com o OpenRouter.
        """
        # Preparar mensagens para o modelo
        formatted_messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Adicionar mensagens do usuário
        for message in messages:
            formatted_messages.append({
                "role": message["role"],
                "content": message["content"]
            })
        
        # Fazer a chamada para o OpenRouter
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.default_model,
                "messages": formatted_messages,
                "temperature": 0.2,
                "max_tokens": 2000
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
                assistant_response = response_data["choices"][0]["message"]["content"]
                
                # Verificar se a resposta contém SQL, chamada de API ou dados de gráfico
                result = {
                    "text": assistant_response
                }
                
                # Extrair SQL (se presente)
                sql_match = re.search(r"```sql\n(.*?)```", assistant_response, re.DOTALL)
                if sql_match:
                    result["sql"] = sql_match.group(1).strip()
                
                # Extrair chamada de API (se presente)
                api_match = re.search(r"```json\n(.*?)```", assistant_response, re.DOTALL)
                if api_match:
                    try:
                        api_json = json.loads(api_match.group(1).strip())
                        result["api_call"] = api_json
                    except json.JSONDecodeError:
                        pass
                
                # Extrair dados de gráfico (se presente)
                chart_match = re.search(r'{"chartType".*?}', assistant_response)
                if chart_match:
                    try:
                        chart_data = json.loads(chart_match.group(0))
                        result["chart_data"] = chart_data
                    except json.JSONDecodeError:
                        pass
                
                # Extrair recomendações (se presentes)
                recommendations = []
                rec_lines = re.findall(r"^\* (.+)$", assistant_response, re.MULTILINE)
                if rec_lines:
                    recommendations = rec_lines
                    result["recommendations"] = recommendations
                
                return result 