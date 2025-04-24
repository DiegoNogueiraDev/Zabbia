import os
import json
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from mcp_server.chains.chat_chain import ChatChain
from mcp_server.chains.sql_chain import SQLGenerationChain
from mcp_server.chains.api_chain import APIGenerationChain
from mcp_server.chains.graph_chain import GraphGenerationChain
from mcp_server.chains.recommendation_chain import RecommendationChain

app = FastAPI(
    title="Zabbia MCP Server",
    description="Servidor MCP para o copiloto de infraestrutura Zabbia",
    version="1.0.0"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restringir para domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instanciar chains
chat_chain = ChatChain()
sql_chain = SQLGenerationChain()
api_chain = APIGenerationChain()
graph_chain = GraphGenerationChain()
recommendation_chain = RecommendationChain()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]
    api_key: str
    context: Optional[Dict[str, Any]] = None

class QueryRequest(BaseModel):
    query: str
    api_key: str

class ActionRequest(BaseModel):
    action: str
    api_key: str

class ContextRequest(BaseModel):
    context: str
    api_key: str

@app.post("/api/chat")
async def process_chat(request: ChatRequest):
    """
    Processa uma mensagem de chat e retorna a resposta.
    """
    try:
        response = await chat_chain.run(
            messages=request.messages,
            api_key=request.api_key,
            context=request.context or {}
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar chat: {str(e)}")

@app.post("/api/generate-sql")
async def generate_sql(request: QueryRequest):
    """
    Gera uma consulta SQL para o Zabbix com base na pergunta em linguagem natural.
    """
    try:
        sql = await sql_chain.run(
            query=request.query,
            api_key=request.api_key
        )
        return {"sql": sql}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar SQL: {str(e)}")

@app.post("/api/generate-api-call")
async def generate_api_call(request: ActionRequest):
    """
    Gera uma chamada para a API JSON-RPC do Zabbix com base na ação em linguagem natural.
    """
    try:
        api_call = await api_chain.run(
            action=request.action,
            api_key=request.api_key
        )
        return {"api_call": api_call}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar chamada API: {str(e)}")

@app.post("/api/generate-graph")
async def generate_graph_data(request: QueryRequest):
    """
    Gera dados para gráfico com base em uma pergunta em linguagem natural.
    """
    try:
        chart_data = await graph_chain.run(
            query=request.query,
            api_key=request.api_key
        )
        return {"chart_data": chart_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar dados de gráfico: {str(e)}")

@app.post("/api/recommend")
async def generate_recommendations(request: ContextRequest):
    """
    Gera recomendações preventivas com base no contexto fornecido.
    """
    try:
        recommendations = await recommendation_chain.run(
            context=request.context,
            api_key=request.api_key
        )
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar recomendações: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Endpoint de verificação de saúde do servidor.
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True) 