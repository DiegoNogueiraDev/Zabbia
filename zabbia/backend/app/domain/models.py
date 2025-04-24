from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import Field, SQLModel, JSON
import uuid

class Base(SQLModel, table=False):
    id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Host(Base, table=True):
    """
    Representa um host no sistema Zabbix.
    """
    host_id: str = Field(index=True)
    name: str = Field(index=True)
    status: int
    ip: Optional[str] = None
    dns: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=JSON)
    
    class Config:
        arbitrary_types_allowed = True

class Metric(Base, table=True):
    """
    Armazena métricas de um host específico.
    """
    host_id: str = Field(foreign_key="host.host_id", index=True)
    item_id: str = Field(index=True)
    timestamp: datetime = Field(index=True)
    key_: str
    value: str
    value_type: int
    units: Optional[str] = None

class Alert(Base, table=True):
    """
    Representa alertas/eventos do Zabbix.
    """
    event_id: str = Field(index=True)
    host_id: str = Field(foreign_key="host.host_id", index=True)
    trigger_id: str = Field(index=True)
    timestamp: datetime = Field(index=True)
    severity: int
    name: str
    description: Optional[str] = None
    status: int
    acknowledged: bool = False
    
class Settings(Base, table=True):
    """
    Armazena configurações do sistema.
    """
    key: str = Field(index=True, unique=True)
    value: str
    
    class Config:
        arbitrary_types_allowed = True

class License(Base, table=True):
    """
    Armazena licenças geradas.
    """
    key: str = Field(index=True, unique=True)
    customer: str
    expires: datetime = Field(index=True)
    seats: int
    revoked: bool = False
    revocation_reason: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True

class ChatHistory(Base, table=True):
    """
    Armazena histórico de conversas.
    """
    user_id: str = Field(index=True)
    session_id: str = Field(index=True, default_factory=lambda: str(uuid.uuid4()))
    message: str
    role: str
    sequence: int = Field(index=True)
    
    class Config:
        arbitrary_types_allowed = True 