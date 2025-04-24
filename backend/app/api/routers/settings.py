from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, SecretStr, validator
from typing import Optional
import os
import json
from sqlmodel import Session

from app.services.database import get_db
from app.domain.models import Settings
from app.services.zabbix import ZabbixService, test_zabbix_connection

router = APIRouter()

class ZabbixSettings(BaseModel):
    url: str
    username: str
    password: SecretStr
    api_token: Optional[SecretStr] = None
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL deve começar com http:// ou https://')
        return v

class OpenRouterSettings(BaseModel):
    api_key: SecretStr

class ZabbixCredentialsResponse(BaseModel):
    url: str
    username: str
    connected: bool

@router.post("/zabbix")
async def save_zabbix_settings(
    settings: ZabbixSettings,
    session: Session = Depends(get_db)
):
    """
    Salva as configurações de conexão com o Zabbix.
    Testa a conexão antes de salvar.
    """
    try:
        # Testar conexão com o Zabbix
        connection_result = await test_zabbix_connection(
            url=settings.url,
            username=settings.username,
            password=settings.password.get_secret_value(),
            api_token=settings.api_token.get_secret_value() if settings.api_token else None
        )
        
        if not connection_result["success"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Falha ao conectar com o Zabbix: {connection_result['error']}"
            )
        
        # Salvar configurações no banco
        db_settings = session.exec(
            select(Settings).where(Settings.key == "zabbix")
        ).first()
        
        if not db_settings:
            db_settings = Settings(
                key="zabbix",
                value=json.dumps({
                    "url": settings.url,
                    "username": settings.username,
                    "password": settings.password.get_secret_value(),
                    "api_token": settings.api_token.get_secret_value() if settings.api_token else None
                })
            )
            session.add(db_settings)
        else:
            db_settings.value = json.dumps({
                "url": settings.url,
                "username": settings.username,
                "password": settings.password.get_secret_value(),
                "api_token": settings.api_token.get_secret_value() if settings.api_token else None
            })
        
        session.commit()
        
        return {
            "message": "Configurações do Zabbix salvas com sucesso",
            "connected": True
        }
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Erro ao salvar configurações: {str(e)}")

@router.get("/zabbix")
async def get_zabbix_settings(
    session: Session = Depends(get_db),
    zabbix_service: ZabbixService = Depends(ZabbixService)
):
    """
    Retorna as configurações de conexão com o Zabbix (sem senhas).
    """
    try:
        db_settings = session.exec(
            select(Settings).where(Settings.key == "zabbix")
        ).first()
        
        if not db_settings:
            return ZabbixCredentialsResponse(
                url="",
                username="",
                connected=False
            )
        
        settings_data = json.loads(db_settings.value)
        
        # Testar conexão atual
        is_connected = await zabbix_service.test_connection()
        
        return ZabbixCredentialsResponse(
            url=settings_data.get("url", ""),
            username=settings_data.get("username", ""),
            connected=is_connected
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar configurações: {str(e)}")

@router.post("/openrouter")
async def save_openrouter_settings(
    settings: OpenRouterSettings,
    session: Session = Depends(get_db)
):
    """
    Salva a chave de API do OpenRouter.
    """
    try:
        # Salvar configurações no banco
        db_settings = session.exec(
            select(Settings).where(Settings.key == "openrouter")
        ).first()
        
        if not db_settings:
            db_settings = Settings(
                key="openrouter",
                value=json.dumps({
                    "api_key": settings.api_key.get_secret_value()
                })
            )
            session.add(db_settings)
        else:
            db_settings.value = json.dumps({
                "api_key": settings.api_key.get_secret_value()
            })
        
        session.commit()
        
        return {
            "message": "Chave de API do OpenRouter salva com sucesso"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar chave de API: {str(e)}")

@router.get("/openrouter")
async def check_openrouter_settings(
    session: Session = Depends(get_db)
):
    """
    Verifica se a chave do OpenRouter está configurada.
    """
    try:
        db_settings = session.exec(
            select(Settings).where(Settings.key == "openrouter")
        ).first()
        
        return {
            "configured": db_settings is not None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar configurações: {str(e)}") 