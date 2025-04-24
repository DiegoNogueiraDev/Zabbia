import pytest
from unittest.mock import Mock, patch, MagicMock
import datetime
import json
from zabbia.backend.services.zabbix_service import ZabbixService

@pytest.fixture
def mock_zabbix_api():
    """Fixture que cria um mock para a API do Zabbix."""
    with patch('zabbia.backend.services.zabbix_service.ZabbixAPI') as mock_api:
        # Configurar o mock da API do Zabbix
        mock_instance = mock_api.return_value
        mock_instance.login.return_value = "123456789"
        
        # Mock para o método do does
        mock_do_request = MagicMock()
        mock_instance.do_request = mock_do_request
        
        yield mock_instance

class TestZabbixService:
    """Testes para o serviço de integração com o Zabbix."""
    
    def test_init_connection(self, mock_zabbix_api):
        """Testa a inicialização da conexão com o Zabbix."""
        # Configurar
        url = "http://zabbix.example.com"
        username = "admin"
        password = "senha123"
        
        # Executar
        service = ZabbixService(url, username, password)
        
        # Verificar
        mock_zabbix_api.assert_called_once_with(url)
        mock_zabbix_api.return_value.login.assert_called_once_with(username, password)
        assert service.api is not None
    
    def test_get_hosts(self, mock_zabbix_api):
        """Testa a obtenção de hosts do Zabbix."""
        # Configurar
        mock_response = {
            "result": [
                {"hostid": "10084", "host": "servidor1", "name": "Servidor Web 1", "status": "0"},
                {"hostid": "10085", "host": "servidor2", "name": "Servidor DB 1", "status": "0"}
            ]
        }
        mock_zabbix_api.return_value.do_request.return_value = mock_response
        
        # Executar
        service = ZabbixService("http://example.com", "user", "pass")
        hosts = service.get_hosts()
        
        # Verificar
        mock_zabbix_api.return_value.do_request.assert_called_once_with('host.get', {
            'output': ['hostid', 'host', 'name', 'status'],
            'selectInterfaces': ['ip']
        })
        assert len(hosts) == 2
        assert hosts[0]['hostid'] == '10084'
        assert hosts[1]['name'] == 'Servidor DB 1'
    
    def test_get_host_by_id(self, mock_zabbix_api):
        """Testa a obtenção de um host específico por ID."""
        # Configurar
        host_id = "10084"
        mock_response = {
            "result": [
                {"hostid": "10084", "host": "servidor1", "name": "Servidor Web 1", "status": "0"}
            ]
        }
        mock_zabbix_api.return_value.do_request.return_value = mock_response
        
        # Executar
        service = ZabbixService("http://example.com", "user", "pass")
        host = service.get_host_by_id(host_id)
        
        # Verificar
        mock_zabbix_api.return_value.do_request.assert_called_once_with('host.get', {
            'output': ['hostid', 'host', 'name', 'status'],
            'hostids': host_id,
            'selectInterfaces': ['ip']
        })
        assert host['hostid'] == '10084'
        assert host['name'] == 'Servidor Web 1'
    
    def test_get_host_items(self, mock_zabbix_api):
        """Testa a obtenção de itens de um host."""
        # Configurar
        host_id = "10084"
        mock_response = {
            "result": [
                {"itemid": "28336", "hostid": "10084", "name": "CPU utilization", "key_": "system.cpu.util", "lastvalue": "45.2"},
                {"itemid": "28337", "hostid": "10084", "name": "Memory usage", "key_": "vm.memory.utilization", "lastvalue": "78.5"}
            ]
        }
        mock_zabbix_api.return_value.do_request.return_value = mock_response
        
        # Executar
        service = ZabbixService("http://example.com", "user", "pass")
        items = service.get_host_items(host_id)
        
        # Verificar
        mock_zabbix_api.return_value.do_request.assert_called_once_with('item.get', {
            'output': ['itemid', 'name', 'key_', 'lastvalue', 'lastclock', 'units'],
            'hostids': host_id,
            'sortfield': 'name'
        })
        assert len(items) == 2
        assert items[0]['name'] == 'CPU utilization'
        assert float(items[1]['lastvalue']) == 78.5
    
    def test_get_problems(self, mock_zabbix_api):
        """Testa a obtenção de problemas ativos."""
        # Configurar
        mock_response = {
            "result": [
                {
                    "eventid": "1001",
                    "objectid": "15022",
                    "name": "High CPU usage on servidor1",
                    "severity": "4",
                    "hosts": [{"hostid": "10084", "name": "Servidor Web 1"}],
                    "clock": "1633872000"
                },
                {
                    "eventid": "1002",
                    "objectid": "15023",
                    "name": "Disk space is low on servidor2",
                    "severity": "3",
                    "hosts": [{"hostid": "10085", "name": "Servidor DB 1"}],
                    "clock": "1633875600"
                }
            ]
        }
        mock_zabbix_api.return_value.do_request.return_value = mock_response
        
        # Executar
        service = ZabbixService("http://example.com", "user", "pass")
        problems = service.get_problems()
        
        # Verificar
        mock_zabbix_api.return_value.do_request.assert_called_once()
        assert len(problems) == 2
        assert problems[0]['name'] == 'High CPU usage on servidor1'
        assert problems[0]['severity'] == '4'
        assert problems[1]['hosts'][0]['name'] == 'Servidor DB 1'
    
    def test_get_history(self, mock_zabbix_api):
        """Testa a obtenção do histórico de valores para um item."""
        # Configurar
        item_id = "28336"
        history_type = 0  # numérico float
        time_from = int((datetime.datetime.now() - datetime.timedelta(hours=24)).timestamp())
        
        mock_response = {
            "result": [
                {"itemid": "28336", "clock": "1633872000", "value": "45.2"},
                {"itemid": "28336", "clock": "1633875600", "value": "48.7"},
                {"itemid": "28336", "clock": "1633879200", "value": "42.1"}
            ]
        }
        mock_zabbix_api.return_value.do_request.return_value = mock_response
        
        # Executar
        service = ZabbixService("http://example.com", "user", "pass")
        history = service.get_history(item_id, history_type, time_from)
        
        # Verificar
        mock_zabbix_api.return_value.do_request.assert_called_once()
        expected_params = {
            'output': 'extend',
            'itemids': item_id,
            'history': history_type,
            'time_from': time_from,
            'sortfield': 'clock',
            'sortorder': 'ASC'
        }
        
        # Verificar se os parâmetros foram passados corretamente
        actual_params = mock_zabbix_api.return_value.do_request.call_args[0][1]
        for key, value in expected_params.items():
            assert key in actual_params
            if key != 'time_from':  # Ignoramos time_from pois é dinâmico
                assert actual_params[key] == value
        
        assert len(history) == 3
        assert history[0]['value'] == '45.2'
        assert history[2]['value'] == '42.1'
    
    def test_get_hosts_with_high_cpu(self, mock_zabbix_api):
        """Testa a obtenção de hosts com CPU alta."""
        # Configurar
        threshold = 80
        period = '1h'
        
        # Simular hosts com itens de CPU
        mock_hosts_response = {
            "result": [
                {"hostid": "10084", "host": "servidor1", "name": "Servidor Web 1"},
                {"hostid": "10085", "host": "servidor2", "name": "Servidor DB 1"}
            ]
        }
        
        # Simular histórico de itens para ambos os hosts
        mock_items_response = {
            "result": [
                {"itemid": "28336", "hostid": "10084", "name": "CPU utilization", "key_": "system.cpu.util"},
                {"itemid": "28337", "hostid": "10085", "name": "CPU utilization", "key_": "system.cpu.util"}
            ]
        }
        
        # Simular histórico para o primeiro host (acima do threshold)
        mock_history_10084 = {
            "result": [
                {"itemid": "28336", "clock": "1633872000", "value": "85.2"},
                {"itemid": "28336", "clock": "1633875600", "value": "88.7"}
            ]
        }
        
        # Simular histórico para o segundo host (abaixo do threshold)
        mock_history_10085 = {
            "result": [
                {"itemid": "28337", "clock": "1633872000", "value": "45.2"},
                {"itemid": "28337", "clock": "1633875600", "value": "48.7"}
            ]
        }
        
        # Configurar o comportamento do mock para retornar diferentes respostas
        def side_effect_func(*args, **kwargs):
            method = args[0]
            params = args[1] if len(args) > 1 else {}
            
            if method == 'host.get':
                return mock_hosts_response
            elif method == 'item.get':
                return mock_items_response
            elif method == 'history.get':
                if 'itemids' in params and params['itemids'] == '28336':
                    return mock_history_10084
                elif 'itemids' in params and params['itemids'] == '28337':
                    return mock_history_10085
            
            return {"result": []}
        
        mock_zabbix_api.return_value.do_request.side_effect = side_effect_func
        
        # Executar
        service = ZabbixService("http://example.com", "user", "pass")
        high_cpu_hosts = service.get_hosts_with_high_cpu(threshold, period)
        
        # Verificar
        assert len(high_cpu_hosts) == 1
        assert high_cpu_hosts[0]['hostid'] == '10084'
        assert high_cpu_hosts[0]['name'] == 'Servidor Web 1'
        assert 'cpu_max' in high_cpu_hosts[0]
        assert high_cpu_hosts[0]['cpu_max'] == '88.7'  # Deve capturar o valor máximo 