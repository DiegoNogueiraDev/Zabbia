from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class BaseResponse(BaseModel):
    """Modelo base para respostas da API"""
    success: bool = True
    message: Optional[str] = None

class ErrorResponse(BaseResponse):
    """Modelo para respostas de erro"""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class ZabbixHost(BaseModel):
    """Modelo representando um host do Zabbix"""
    hostid: str
    host: str
    name: Optional[str] = None
    status: Optional[str] = None
    available: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        orm_mode = True

class ZabbixItem(BaseModel):
    """Modelo representando um item do Zabbix"""
    itemid: str
    hostid: str
    name: str
    key_: str
    value_type: str
    units: Optional[str] = None
    lastvalue: Optional[str] = None
    
    class Config:
        orm_mode = True

class ZabbixHistoryItem(BaseModel):
    """Modelo representando um item de histórico do Zabbix"""
    clock: int
    value: str
    itemid: str
    
    def get_datetime(self) -> datetime:
        """Converte o timestamp unix para datetime"""
        return datetime.fromtimestamp(int(self.clock))
    
    class Config:
        orm_mode = True

class ZabbixProblem(BaseModel):
    """Modelo representando um problema do Zabbix"""
    eventid: str
    objectid: str
    name: str
    severity: str
    clock: int
    r_clock: Optional[int] = None  # Recovery time
    acknowledged: str
    
    def get_datetime(self) -> datetime:
        """Converte o timestamp unix para datetime"""
        return datetime.fromtimestamp(int(self.clock))
    
    def get_recovery_datetime(self) -> Optional[datetime]:
        """Converte o timestamp unix de recuperação para datetime"""
        if self.r_clock:
            return datetime.fromtimestamp(int(self.r_clock))
        return None
    
    class Config:
        orm_mode = True

class ZabbixTrigger(BaseModel):
    """Modelo representando um trigger do Zabbix"""
    triggerid: str
    description: str
    expression: str
    value: str
    priority: str
    lastchange: Optional[str] = None
    state: Optional[str] = None
    
    class Config:
        orm_mode = True

class HostsResponse(BaseResponse):
    """Resposta contendo lista de hosts"""
    data: List[ZabbixHost]
    total: int = Field(..., description="Total de hosts retornados")

class ItemsResponse(BaseResponse):
    """Resposta contendo lista de itens"""
    data: List[ZabbixItem]
    total: int = Field(..., description="Total de itens retornados")

class HistoryResponse(BaseResponse):
    """Resposta contendo histórico de um item"""
    data: List[ZabbixHistoryItem]
    total: int = Field(..., description="Total de registros históricos retornados")
    item_details: Optional[ZabbixItem] = None

class ProblemsResponse(BaseResponse):
    """Resposta contendo problemas ativos"""
    data: List[ZabbixProblem]
    total: int = Field(..., description="Total de problemas retornados")

class TriggersResponse(BaseResponse):
    """Resposta contendo triggers"""
    data: List[ZabbixTrigger]
    total: int = Field(..., description="Total de triggers retornados")

class QueryRequest(BaseModel):
    """Modelo para solicitar uma consulta ao Zabbix"""
    query: str = Field(..., description="A pergunta em linguagem natural")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Contexto adicional opcional")
    
class QueryResponse(BaseResponse):
    """Resposta para consultas em linguagem natural"""
    data: Dict[str, Any] = Field(..., description="Dados da resposta")
    sql: Optional[str] = Field(default=None, description="SQL gerado para a consulta")
    chart_data: Optional[Dict[str, Any]] = Field(default=None, description="Dados para geração de gráficos")
    explanation: Optional[str] = Field(default=None, description="Explicação da resposta") 