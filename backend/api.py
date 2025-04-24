import logging
import json
import os
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from time import time

from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from zabbia.backend.config import settings
from zabbia.backend.zabbix_api import api_client, ZabbixAPIException
from zabbia.backend.nlp_processor import nlp_processor, QueryIntent

# Configuração de logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="Zabbia API",
    description="API para o Zabbia - Copiloto de Infraestrutura para Zabbix",
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporariamente permitir todas as origens para desenvolvimento
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de dados Pydantic
class ZabbiaQuery(BaseModel):
    """Modelo para consulta em linguagem natural ao Zabbia"""
    query: str = Field(..., description="Consulta em linguagem natural")
    conversation_id: Optional[str] = Field(None, description="ID da conversa para manter contexto")

class ZabbiaResponse(BaseModel):
    """Modelo para resposta do Zabbia"""
    response: str = Field(..., description="Resposta em texto")
    data: Optional[Dict[str, Any]] = Field(None, description="Dados estruturados (se aplicável)")
    sql: Optional[str] = Field(None, description="SQL executado (se aplicável)")
    charts: Optional[List[Dict[str, Any]]] = Field(None, description="Dados de gráficos (se aplicável)")
    conversation_id: Optional[str] = Field(None, description="ID da conversa")

class MaintenanceRequest(BaseModel):
    """Modelo para requisição de manutenção"""
    host_ids: List[str] = Field(..., description="IDs dos hosts para manutenção")
    duration_minutes: int = Field(60, description="Duração da manutenção em minutos")
    description: Optional[str] = Field(None, description="Descrição da manutenção")

class MaintenanceResponse(BaseModel):
    """Modelo para resposta de manutenção"""
    maintenance_id: str = Field(..., description="ID da manutenção criada")
    hosts: List[str] = Field(..., description="Nomes dos hosts em manutenção")
    start_time: str = Field(..., description="Hora de início (ISO format)")
    end_time: str = Field(..., description="Hora de término (ISO format)")

# Middleware para verificação de licença
@app.middleware("http")
async def verify_license(request: Request, call_next):
    """Verifica se há uma licença válida para acessar a API"""
    # Pular verificação para rotas de documentação e status
    if request.url.path.startswith(("/docs", "/redoc", "/openapi.json", "/status")):
        return await call_next(request)
    
    # Verificar token de licença
    license_key = request.headers.get("X-License-Key")
    
    if not settings.is_development:
        if not license_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Chave de licença não fornecida"}
            )
        
        # Em um sistema real, aqui verificaríamos a validade da licença
        # Como exemplo, vamos considerar válida se não for vazia
        if license_key.strip() == "":
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Chave de licença inválida"}
            )
    
    return await call_next(request)

# Rota para verificar status da API
@app.get("/status", tags=["Sistema"])
async def check_status():
    """Verifica o status da API e conexão com o Zabbix"""
    try:
        # Tentar obter informação básica do Zabbix
        api_version = api_client.api_call("apiinfo.version")
        
        return {
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "api_version": settings.api_version,
            "zabbix_version": api_version,
            "environment": settings.environment
        }
    except Exception as e:
        logger.error(f"Erro ao verificar status: {str(e)}")
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "api_version": settings.api_version,
            "error": str(e),
            "environment": settings.environment
        }

# Rota para processar consulta em linguagem natural
@app.post("/query", response_model=ZabbiaResponse, tags=["Consultas"])
async def process_query(request: ZabbiaQuery):
    """Processa uma consulta em linguagem natural e retorna a resposta"""
    start_time = time()
    query = request.query
    
    try:
        # Identificar intenção da consulta
        intent = nlp_processor.detect_intent(query)
        logger.info(f"Intenção detectada: {intent} para consulta: '{query}'")
        
        # Extrair parâmetros relevantes
        host = nlp_processor.extract_host(query)
        time_range = nlp_processor.extract_time_range(query)
        
        response_text = ""
        data = {}
        sql = None
        charts = None
        
        # Processar conforme a intenção
        if intent == QueryIntent.GRAPH_REQUEST:
            # Gerar dados para gráfico
            chart_data = nlp_processor.generate_graph_data(query)
            
            # Em um sistema real, buscaríamos os dados históricos
            # e preencheríamos o chart_data com dados reais
            
            # Preencher com alguns dados simulados para exemplo
            now = datetime.now()
            chart_data["labels"] = [
                (now - timedelta(hours=i)).strftime("%H:%M") 
                for i in range(12, 0, -1)
            ]
            
            import random
            if len(chart_data["datasets"]) > 0:
                chart_data["datasets"][0]["data"] = [
                    random.randint(10, 90) for _ in range(12)
                ]
                
            charts = [chart_data]
            response_text = f"Aqui está o gráfico solicitado para {chart_data['title']}"
            
        elif intent == QueryIntent.HOST_MAINTENANCE:
            # Processar solicitação de manutenção
            if not host:
                response_text = "Por favor, especifique qual host deseja colocar em manutenção."
            else:
                # Buscar ID do host pelo nome
                host_obj = api_client.get_host_by_name(host)
                
                if not host_obj:
                    response_text = f"Host '{host}' não encontrado no Zabbix."
                else:
                    duration = nlp_processor.extract_duration(query, 60)  # Minutos
                    
                    # Colocar em manutenção
                    maintenance_id = api_client.set_host_maintenance(
                        host_obj["hostid"],
                        name=f"Manutenção via Zabbia - {host}",
                        duration=duration * 60  # Converter para segundos
                    )
                    
                    if maintenance_id:
                        response_text = f"Host {host} colocado em manutenção por {duration} minutos."
                        data = {
                            "maintenance_id": maintenance_id,
                            "host": host,
                            "duration_minutes": duration
                        }
                    else:
                        response_text = f"Erro ao colocar host {host} em manutenção."
                        
        elif intent in [QueryIntent.HIGH_CPU, QueryIntent.MEMORY_USAGE, 
                        QueryIntent.HOST_STATUS, QueryIntent.HOST_UPTIME,
                        QueryIntent.UNAVAILABLE_SERVICES, QueryIntent.ALERT_SUMMARY]:
            # Gerar SQL para a consulta
            generated_sql, context = nlp_processor.generate_sql(query)
            sql = generated_sql
            
            # Em um sistema real, executaríamos o SQL no banco do Zabbix
            # e preencheríamos o data com o resultado
            
            # Para o exemplo, vamos simular dados
            if intent == QueryIntent.HIGH_CPU:
                data = {
                    "hosts": [
                        {"name": "web01.example.com", "cpu_usage": 92.5},
                        {"name": "web02.example.com", "cpu_usage": 88.7},
                        {"name": "db01.example.com", "cpu_usage": 85.3}
                    ],
                    "count": 3,
                    "threshold": context.get("threshold", 80)
                }
                response_text = f"Encontrados {data['count']} hosts com CPU acima de {data['threshold']}%."
                
            elif intent == QueryIntent.HOST_STATUS:
                data = {
                    "hosts": [
                        {"name": "web01.example.com", "status": "Enabled", "availability": "Available"},
                        {"name": "web02.example.com", "status": "Enabled", "availability": "Available"},
                        {"name": "db01.example.com", "status": "Enabled", "availability": "Available"},
                        {"name": "monitor01.example.com", "status": "Enabled", "availability": "Unavailable"}
                    ],
                    "count": 4,
                    "available": 3,
                    "unavailable": 1
                }
                response_text = f"Status atual dos hosts: {data['available']} disponíveis, {data['unavailable']} indisponíveis."
                
            elif intent == QueryIntent.UNAVAILABLE_SERVICES:
                data = {
                    "services": [
                        {
                            "host": "web01.example.com", 
                            "service": "HTTP Service", 
                            "since": "2023-06-15T14:30:00"
                        },
                        {
                            "host": "db01.example.com", 
                            "service": "MySQL Service", 
                            "since": "2023-06-15T15:45:00"
                        }
                    ],
                    "count": 2
                }
                response_text = f"Há {data['count']} serviços indisponíveis atualmente."
                
            elif intent == QueryIntent.HOST_UPTIME:
                host_name = host if host else "todos os hosts"
                data = {
                    "hosts": [
                        {"name": "web01.example.com", "uptime_days": 45.2},
                        {"name": "web02.example.com", "uptime_days": 12.7},
                        {"name": "db01.example.com", "uptime_days": 78.5}
                    ]
                }
                response_text = f"Uptime para {host_name}:"
                
            elif intent == QueryIntent.ALERT_SUMMARY:
                data = {
                    "alerts": [
                        {"host": "web01.example.com", "problem": "CPU alto", "severity": "High"},
                        {"host": "db01.example.com", "problem": "Disco cheio", "severity": "Disaster"},
                        {"host": "web02.example.com", "problem": "Serviço HTTP indisponível", "severity": "Average"}
                    ],
                    "count": 3,
                    "by_severity": {
                        "Disaster": 1,
                        "High": 1,
                        "Average": 1
                    }
                }
                response_text = f"Resumo de alertas: {data['count']} problemas ativos, incluindo {data['by_severity'].get('Disaster', 0)} críticos."
                
        else:
            # Consulta genérica - Buscar informações básicas
            method, params = nlp_processor.generate_api_call(query)
            
            if method:
                try:
                    # Em um sistema real, faríamos a chamada à API
                    # api_result = api_client.api_call(method, params)
                    
                    # Para o exemplo, vamos simular dados
                    data = {
                        "hosts": [
                            {"name": "web01.example.com", "status": "Enabled"},
                            {"name": "web02.example.com", "status": "Enabled"},
                            {"name": "db01.example.com", "status": "Enabled"}
                        ],
                        "count": 3
                    }
                    response_text = f"Encontrados {data['count']} hosts no sistema."
                    
                except ZabbixAPIException as e:
                    response_text = f"Erro ao consultar o Zabbix: {str(e)}"
            else:
                response_text = "Não consegui entender sua consulta. Pode reformular de outra forma?"
        
        # Calcular tempo de processamento
        processing_time = time() - start_time
        logger.info(f"Consulta processada em {processing_time:.2f} segundos")
        
        # Adicionar informação de tempo de processamento na resposta se não for produção
        if settings.environment != "production":
            response_text += f"\n\nConsulta processada em {processing_time:.2f} segundos."
        
        return ZabbiaResponse(
            response=response_text,
            data=data,
            sql=sql,
            charts=charts,
            conversation_id=request.conversation_id or f"zabbia-{int(time())}"
        )
        
    except Exception as e:
        logger.error(f"Erro ao processar consulta: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar consulta: {str(e)}"
        )

# Rota para buscar hosts
@app.get("/hosts", tags=["Zabbix"])
async def get_hosts(search: Optional[str] = None):
    """Obtém a lista de hosts do Zabbix"""
    try:
        filter_data = {}
        if search:
            filter_data = {
                "search": {"name": search},
                "searchWildcardsEnabled": True
            }
            
        hosts = api_client.get_hosts(filter_data)
        return {"hosts": hosts, "count": len(hosts)}
    except ZabbixAPIException as e:
        logger.error(f"Erro ao buscar hosts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar hosts: {str(e)}"
        )

# Rota para buscar problemas
@app.get("/problems", tags=["Zabbix"])
async def get_problems(severity_from: Optional[int] = None, severity_till: Optional[int] = None):
    """Obtém a lista de problemas ativos no Zabbix"""
    try:
        problems = api_client.get_problems(severity_from, severity_till)
        return {"problems": problems, "count": len(problems)}
    except ZabbixAPIException as e:
        logger.error(f"Erro ao buscar problemas: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar problemas: {str(e)}"
        )

# Rota para colocar hosts em manutenção
@app.post("/maintenance", response_model=MaintenanceResponse, tags=["Zabbix"])
async def create_maintenance(request: MaintenanceRequest):
    """Coloca hosts em modo de manutenção"""
    try:
        host_names = []
        
        # Buscar nomes dos hosts pelo ID
        for host_id in request.host_ids:
            hosts = api_client.get_hosts({"filter": {"hostid": host_id}})
            if hosts:
                host_names.append(hosts[0]["name"])
        
        # Definir horários
        now = datetime.now()
        end_time = now + timedelta(minutes=request.duration_minutes)
        
        # Criar manutenção
        maintenance_id = api_client.set_host_maintenance(
            request.host_ids,
            name=f"Manutenção via Zabbia API",
            duration=request.duration_minutes * 60,  # Converter para segundos
            type_=0  # 0 = com coleta de dados
        )
        
        if not maintenance_id:
            raise HTTPException(
                status_code=500,
                detail="Erro ao criar manutenção"
            )
            
        return MaintenanceResponse(
            maintenance_id=maintenance_id,
            hosts=host_names,
            start_time=now.isoformat(),
            end_time=end_time.isoformat()
        )
    except ZabbixAPIException as e:
        logger.error(f"Erro ao criar manutenção: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar manutenção: {str(e)}"
        )

# Rota para obter dados de dashboard
@app.get("/dashboard", tags=["Zabbix"])
async def get_dashboard():
    """Obtém dados resumidos para o dashboard"""
    try:
        dashboard_data = api_client.get_dashboard_data()
        return dashboard_data
    except ZabbixAPIException as e:
        logger.error(f"Erro ao obter dados do dashboard: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter dados do dashboard: {str(e)}"
        )

# Evento de inicialização e encerramento
@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização do servidor"""
    logger.info(f"Iniciando API Zabbia v{settings.api_version} em ambiente {settings.environment}")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento executado no encerramento do servidor"""
    logger.info("Encerrando API Zabbia")
    api_client.close() 