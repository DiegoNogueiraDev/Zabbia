from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import grpc
import json

from app.services.mcp_client import MCPClient, get_mcp_client

router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    sql: Optional[str] = None
    api_call: Optional[dict] = None
    chart_data: Optional[dict] = None
    recommendations: Optional[List[str]] = None

@router.post("", response_model=ChatResponse)
async def process_chat(
    chat_request: ChatRequest,
    background_tasks: BackgroundTasks,
    mcp_client: MCPClient = Depends(get_mcp_client)
):
    """
    Processa uma requisição de chat, enviando-a para o servidor MCP.
    Retorna a resposta natural e opcionalmente SQL, chamadas API ou dados de gráficos.
    """
    try:
        # Extrair a última mensagem do usuário
        user_messages = [m for m in chat_request.messages if m.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="Nenhuma mensagem do usuário encontrada")
        
        last_user_message = user_messages[-1].content
        
        # Verificar comandos especiais
        if last_user_message.startswith("/generate-sql"):
            query = last_user_message.replace("/generate-sql", "").strip()
            result = await mcp_client.generate_sql(query)
            return ChatResponse(
                response=f"SQL gerado para: {query}",
                sql=result
            )
        
        elif last_user_message.startswith("/call-api"):
            action = last_user_message.replace("/call-api", "").strip()
            result = await mcp_client.generate_api_call(action)
            return ChatResponse(
                response=f"Chamada API gerada para: {action}",
                api_call=result
            )
        
        elif last_user_message.startswith("/graph"):
            query = last_user_message.replace("/graph", "").strip()
            result = await mcp_client.generate_graph_data(query)
            return ChatResponse(
                response=f"Dados de gráfico gerados para: {query}",
                chart_data=result
            )
        
        elif last_user_message.startswith("/recommend"):
            context = last_user_message.replace("/recommend", "").strip()
            result = await mcp_client.generate_recommendations(context)
            return ChatResponse(
                response="Recomendações baseadas no contexto fornecido:",
                recommendations=result
            )
        
        # Mensagem normal de chat
        else:
            full_history = [{"role": m.role, "content": m.content} for m in chat_request.messages]
            
            # Se houver ID de usuário, adicionar ao histórico para contexto
            context = {}
            if chat_request.user_id:
                context["user_id"] = chat_request.user_id
            
            # Processamento assíncrono da resposta
            response = await mcp_client.process_chat(
                messages=full_history,
                context=context
            )
            
            # Salvar conversa em background para histórico
            if chat_request.user_id:
                background_tasks.add_task(
                    mcp_client.save_conversation,
                    user_id=chat_request.user_id,
                    messages=full_history + [{"role": "assistant", "content": response.get("text", "")}]
                )
            
            # Construir resposta
            return ChatResponse(
                response=response.get("text", ""),
                sql=response.get("sql"),
                api_call=response.get("api_call"),
                chart_data=response.get("chart_data"),
                recommendations=response.get("recommendations")
            )
    
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"Erro de comunicação com o servidor MCP: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar chat: {str(e)}")

@router.get("/history/{user_id}")
async def get_chat_history(
    user_id: str,
    limit: int = 10,
    mcp_client: MCPClient = Depends(get_mcp_client)
):
    """
    Obtém o histórico de conversas de um usuário específico.
    """
    try:
        history = await mcp_client.get_conversation_history(user_id=user_id, limit=limit)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar histórico: {str(e)}") 