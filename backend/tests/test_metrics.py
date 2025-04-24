import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, MagicMock

from app.main import app
from app.services.zabbix import ZabbixService

client = TestClient(app)

@pytest.fixture
def mock_zabbix_service():
    with patch("app.api.routers.metrics.ZabbixService") as mock:
        # Configurar mock para retornar dados simulados
        instance = mock.return_value
        
        # Host ativos
        instance.get_active_hosts.return_value = [
            {"hostid": "10001", "name": "web01", "status": 0},
            {"hostid": "10002", "name": "db01", "status": 0},
        ]
        
        # Métricas de CPU
        instance.get_cpu_metrics.return_value = [
            {
                "host_id": "10001",
                "data": [
                    {"timestamp": "2023-10-01T12:00:00", "value": 45.5},
                    {"timestamp": "2023-10-01T12:05:00", "value": 52.3},
                ]
            }
        ]
        
        # Métricas de memória
        instance.get_memory_metrics.return_value = [
            {
                "host_id": "10001",
                "data": [
                    {"timestamp": "2023-10-01T12:00:00", "value": 65.2},
                    {"timestamp": "2023-10-01T12:05:00", "value": 67.8},
                ]
            }
        ]
        
        # Métricas de disponibilidade
        instance.get_availability_metrics.return_value = [
            {
                "host_id": "10001",
                "data": {
                    "availability_percent": 99.8,
                    "total_downtime_seconds": 72,
                    "events": []
                }
            }
        ]
        
        # Uptime médio
        instance.get_average_uptime.return_value = 99.9
        
        # Hosts em alerta
        instance.get_hosts_in_alert.return_value = [
            {
                "host_id": "10002",
                "name": "db01",
                "alerts": [
                    {
                        "name": "Alta utilização de CPU",
                        "priority": 3,
                        "since": "2023-10-01T11:45:00"
                    }
                ]
            }
        ]
        
        yield instance

@pytest.mark.asyncio
async def test_get_metrics_overview(mock_zabbix_service):
    """
    Testa o endpoint de visão geral de métricas.
    """
    # Injeta o mock no app
    app.dependency_overrides[ZabbixService] = lambda: mock_zabbix_service
    
    # Fazer a requisição
    response = client.get("/api/metrics/overview")
    
    # Verificar a resposta
    assert response.status_code == 200
    data = response.json()
    
    # Verificar estrutura da resposta
    assert "hosts" in data
    assert "metrics" in data
    assert "avg_uptime" in data
    assert "hosts_in_alert" in data
    
    # Verificar dados específicos
    assert len(data["hosts"]) == 2
    assert data["hosts"][0]["name"] == "web01"
    assert data["avg_uptime"] == 99.9
    assert len(data["hosts_in_alert"]) == 1
    assert data["hosts_in_alert"][0]["name"] == "db01"
    
    # Limpar override
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_high_cpu_hosts(mock_zabbix_service):
    """
    Testa o endpoint de hosts com CPU alta.
    """
    # Configurar mock para este teste específico
    mock_zabbix_service.get_hosts_with_high_cpu.return_value = [
        {"hostid": "10001", "name": "web01", "cpu": 92.5},
        {"hostid": "10003", "name": "app01", "cpu": 87.3},
    ]
    
    # Injeta o mock no app
    app.dependency_overrides[ZabbixService] = lambda: mock_zabbix_service
    
    # Fazer a requisição
    response = client.get("/api/metrics/high-cpu?threshold=85&period_minutes=15")
    
    # Verificar a resposta
    assert response.status_code == 200
    data = response.json()
    
    # Verificar estrutura da resposta
    assert "hosts" in data
    assert "query" in data
    assert data["query"]["threshold"] == 85
    assert data["query"]["period_minutes"] == 15
    
    # Verificar dados específicos
    assert len(data["hosts"]) == 2
    assert data["hosts"][0]["name"] == "web01"
    assert data["hosts"][0]["cpu"] == 92.5
    
    # Verificar se o método foi chamado com os parâmetros corretos
    mock_zabbix_service.get_hosts_with_high_cpu.assert_called_once_with(
        threshold=85, period_minutes=15
    )
    
    # Limpar override
    app.dependency_overrides.clear() 