import os
import json
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import Depends
from sqlmodel import Session, select
import grpc

from app.services.database import get_db
from app.domain.models import ChatHistory, Settings

class MCPClient:
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session
        self._api_key = None
        self._http_session = None
        self._mcp_server_url = os.getenv("MCP_SERVER_URL", "http://mcp:8080")
    
    async def _get_api_key(self) -> str:
        """
        Obtém a chave de API do OpenRouter das configurações.
        """
        if self._api_key is not None:
            return self._api_key
        
        settings = self.session.exec(
            select(Settings).where(Settings.key == "openrouter")
        ).first()
        
        if not settings:
            raise ValueError("Chave de API do OpenRouter não configurada")
        
        settings_data = json.loads(settings.value)
        self._api_key = settings_data.get("api_key")
        
        if not self._api_key:
            raise ValueError("Chave de API do OpenRouter não encontrada")
        
        return self._api_key
    
    def _get_session(self) -> aiohttp.ClientSession:
        """
        Retorna uma sessão HTTP para comunicação com o servidor MCP.
        """
        if self._http_session is None or self._http_session.closed:
            self._http_session = aiohttp.ClientSession()
        
        return self._http_session
    
    async def process_chat(self, messages: List[Dict[str, Any]], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Envia mensagens para o servidor MCP e retorna a resposta.
        """
        api_key = await self._get_api_key()
        session = self._get_session()
        
        payload = {
            "messages": messages,
            "api_key": api_key,
            "context": context or {}
        }
        
        async with session.post(f"{self._mcp_server_url}/api/chat", json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise ValueError(f"Erro ao processar chat: {error_text}")
            
            result = await response.json()
            return result
    
    async def generate_sql(self, query: str) -> str:
        """
        Gera uma consulta SQL para o Zabbix com base na pergunta em linguagem natural.
        """
        api_key = await self._get_api_key()
        session = self._get_session()
        
        payload = {
            "query": query,
            "api_key": api_key
        }
        
        async with session.post(f"{self._mcp_server_url}/api/generate-sql", json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise ValueError(f"Erro ao gerar SQL: {error_text}")
            
            result = await response.json()
            return result.get("sql", "")
    
    async def generate_api_call(self, action: str) -> Dict[str, Any]:
        """
        Gera uma chamada para a API JSON-RPC do Zabbix com base na ação em linguagem natural.
        """
        api_key = await self._get_api_key()
        session = self._get_session()
        
        payload = {
            "action": action,
            "api_key": api_key
        }
        
        async with session.post(f"{self._mcp_server_url}/api/generate-api-call", json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise ValueError(f"Erro ao gerar chamada API: {error_text}")
            
            result = await response.json()
            return result.get("api_call", {})
    
    async def generate_graph_data(self, query: str) -> Dict[str, Any]:
        """
        Gera dados para gráfico com base em uma pergunta em linguagem natural.
        """
        api_key = await self._get_api_key()
        session = self._get_session()
        
        payload = {
            "query": query,
            "api_key": api_key
        }
        
        async with session.post(f"{self._mcp_server_url}/api/generate-graph", json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise ValueError(f"Erro ao gerar dados de gráfico: {error_text}")
            
            result = await response.json()
            return result.get("chart_data", {})
    
    async def generate_recommendations(self, context: str) -> List[str]:
        """
        Gera recomendações preventivas com base no contexto fornecido.
        """
        api_key = await self._get_api_key()
        session = self._get_session()
        
        payload = {
            "context": context,
            "api_key": api_key
        }
        
        async with session.post(f"{self._mcp_server_url}/api/recommend", json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise ValueError(f"Erro ao gerar recomendações: {error_text}")
            
            result = await response.json()
            return result.get("recommendations", [])
    
    async def save_conversation(self, user_id: str, messages: List[Dict[str, str]]) -> None:
        """
        Salva uma conversa no histórico.
        """
        try:
            # Gerar um ID de sessão único para esta conversa
            session_id = f"{user_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            # Adicionar cada mensagem ao histórico
            for idx, message in enumerate(messages):
                chat_history = ChatHistory(
                    user_id=user_id,
                    session_id=session_id,
                    message=message["content"],
                    role=message["role"],
                    sequence=idx
                )
                self.session.add(chat_history)
            
            self.session.commit()
        
        except Exception as e:
            # Logar erro, mas não quebrar o fluxo principal
            print(f"Erro ao salvar conversa: {str(e)}")
    
    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recupera histórico de conversas de um usuário.
        """
        # Obter sessões únicas para este usuário (ordenadas por mais recentes)
        sessions = self.session.exec(
            select(ChatHistory.session_id)
            .where(ChatHistory.user_id == user_id)
            .distinct()
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
        ).all()
        
        result = []
        
        # Para cada sessão, buscar todas as mensagens
        for session_id in sessions:
            messages = self.session.exec(
                select(ChatHistory)
                .where(ChatHistory.session_id == session_id)
                .order_by(ChatHistory.sequence)
            ).all()
            
            # Agrupar mensagens da sessão
            if messages:
                first_message = messages[0]
                
                session_data = {
                    "session_id": session_id,
                    "timestamp": first_message.created_at.isoformat(),
                    "messages": [
                        {
                            "role": msg.role,
                            "content": msg.message,
                            "timestamp": msg.created_at.isoformat()
                        }
                        for msg in messages
                    ]
                }
                
                result.append(session_data)
        
        return result
    
    async def close(self):
        """
        Fecha a sessão HTTP quando o cliente não for mais necessário.
        """
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()
            self._http_session = None

def get_mcp_client(session: Session = Depends(get_db)) -> MCPClient:
    """
    Factory para obter um cliente MCP com sessão de banco de dados.
    """
    return MCPClient(session=session) 