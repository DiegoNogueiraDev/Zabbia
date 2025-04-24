import os
import aiohttp
from typing import Dict, Any, List
import re

class RecommendationChain:
    def __init__(self):
        self.openrouter_endpoint = "https://openrouter.ai/api/v1/chat/completions"
        self.default_model = "openai/gpt-4o-mini"
        
        # Carregar sistema de prompts
        self.system_prompt = """Você é um especialista em administração de sistemas e monitoramento Zabbix.
Sua tarefa é gerar recomendações preventivas com base no contexto fornecido pelo usuário.

Siga estas diretrizes:
1. Analise o contexto para identificar possíveis problemas ou pontos de melhoria
2. Gere recomendações específicas, práticas e aplicáveis
3. Direcione as recomendações para otimização de desempenho, estabilidade ou segurança
4. Inclua justificativas breves para cada recomendação
5. Considere boas práticas de monitoramento e administração de sistemas
6. Sugira limiares (thresholds) apropriados para alertas quando relevante
7. Proponha automações de remediação quando aplicável

Tipos de recomendação:
- Ajuste de thresholds de alertas
- Configuração de monitoramento adicional
- Otimização de recursos (CPU, memória, disco)
- Melhores práticas de segurança
- Escalada e notificações
- Estratégias de backup
- Atualizações de sistema

Em sua resposta, forneça APENAS uma lista de recomendações, cada uma em uma linha começando com "*".
"""
    
    async def run(self, context: str, api_key: str) -> List[str]:
        """
        Executa a chain de recomendações com o OpenRouter.
        """
        # Preparar mensagens para o modelo
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": context}
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
                "temperature": 0.4,
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
                rec_response = response_data["choices"][0]["message"]["content"]
                
                # Extrair recomendações (linhas que começam com "*")
                recommendations = []
                for line in rec_response.split("\n"):
                    line = line.strip()
                    if line.startswith("*"):
                        recommendations.append(line[1:].strip())
                
                # Se nenhuma recomendação foi extraída no formato esperado,
                # tratar a resposta completa como uma única recomendação
                if not recommendations and rec_response.strip():
                    recommendations = [rec_response.strip()]
                
                return recommendations 