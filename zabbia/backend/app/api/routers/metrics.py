from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from sqlmodel import Session, select

from app.domain.models import Host, Metric
from app.services.zabbix import ZabbixService
from app.services.database import get_db

router = APIRouter()

@router.get("/overview")
async def get_metrics_overview(
    session: Session = Depends(get_db),
    zabbix_service: ZabbixService = Depends(ZabbixService)
):
    """
    Retorna uma visão geral das métricas principais para o dashboard.
    Inclui CPU, RAM, e disponibilidade de todos os hosts.
    """
    try:
        # Obter dados dos últimos hosts ativos
        hosts = await zabbix_service.get_active_hosts()
        
        # Obter métricas de CPU, RAM e disponibilidade
        cpu_metrics = await zabbix_service.get_cpu_metrics(hours=24)
        memory_metrics = await zabbix_service.get_memory_metrics(hours=24)
        availability_metrics = await zabbix_service.get_availability_metrics(hours=24)
        
        # Calcular uptime médio
        avg_uptime = await zabbix_service.get_average_uptime()
        
        # Hosts em alerta
        hosts_in_alert = await zabbix_service.get_hosts_in_alert()
        
        return {
            "hosts": hosts,
            "metrics": {
                "cpu": cpu_metrics,
                "memory": memory_metrics,
                "availability": availability_metrics
            },
            "avg_uptime": avg_uptime,
            "hosts_in_alert": hosts_in_alert
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter métricas: {str(e)}")

@router.get("/{host}")
async def get_host_metrics(
    host: str,
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    zabbix_service: ZabbixService = Depends(ZabbixService)
):
    """
    Retorna métricas específicas para um host.
    Permite filtrar por período.
    """
    if not from_date:
        from_date = datetime.now() - timedelta(hours=24)
    
    if not to_date:
        to_date = datetime.now()
    
    try:
        # Obter detalhes do host
        host_details = await zabbix_service.get_host_details(host)
        
        if not host_details:
            raise HTTPException(status_code=404, detail=f"Host '{host}' não encontrado")
        
        # Obter métricas para o host no período especificado
        metrics = await zabbix_service.get_host_metrics(
            host_id=host_details["hostid"],
            from_date=from_date,
            to_date=to_date
        )
        
        return {
            "host": host_details,
            "metrics": metrics,
            "period": {
                "from": from_date.isoformat(),
                "to": to_date.isoformat()
            }
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Erro ao obter métricas do host: {str(e)}")

@router.get("/high-cpu")
async def get_high_cpu_hosts(
    threshold: int = Query(80, ge=1, le=100),
    period_minutes: int = Query(30, ge=5, le=1440),
    zabbix_service: ZabbixService = Depends(ZabbixService)
):
    """
    Retorna hosts com uso de CPU acima do limite especificado.
    """
    try:
        high_cpu_hosts = await zabbix_service.get_hosts_with_high_cpu(
            threshold=threshold,
            period_minutes=period_minutes
        )
        
        return {
            "hosts": high_cpu_hosts,
            "query": {
                "threshold": threshold,
                "period_minutes": period_minutes
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter hosts com CPU alta: {str(e)}") 