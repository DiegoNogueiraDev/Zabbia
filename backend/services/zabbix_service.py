import time
import datetime
from typing import List, Dict, Any, Optional, Union
from pyzabbix import ZabbixAPI
from ..config import settings

class ZabbixService:
    """
    Serviço para integração com a API do Zabbix.
    Facilita consultas e operações no Zabbix através de métodos em linguagem natural.
    """
    
    def __init__(self, url: str, username: str, password: str):
        """
        Inicializa a conexão com o Zabbix API.
        
        Args:
            url: URL do servidor Zabbix
            username: Nome de usuário para autenticação
            password: Senha para autenticação
        """
        self.api = ZabbixAPI(url)
        self.api.login(username, password)
        self.api.timeout = 10.0
    
    def get_hosts(self) -> List[Dict[str, Any]]:
        """
        Obtém todos os hosts cadastrados no Zabbix.
        
        Returns:
            Lista de hosts com seus detalhes
        """
        return self.api.do_request('host.get', {
            'output': ['hostid', 'host', 'name', 'status'],
            'selectInterfaces': ['ip']
        })['result']
    
    def get_host_by_id(self, host_id: str) -> Dict[str, Any]:
        """
        Obtém detalhes de um host específico pelo ID.
        
        Args:
            host_id: ID do host no Zabbix
            
        Returns:
            Detalhes do host
        """
        hosts = self.api.do_request('host.get', {
            'output': ['hostid', 'host', 'name', 'status'],
            'hostids': host_id,
            'selectInterfaces': ['ip']
        })['result']
        
        if hosts:
            return hosts[0]
        return {}
    
    def get_host_by_name(self, host_name: str) -> Dict[str, Any]:
        """
        Obtém detalhes de um host pelo nome ou hostname.
        
        Args:
            host_name: Nome ou hostname do host
            
        Returns:
            Detalhes do host
        """
        hosts = self.api.do_request('host.get', {
            'output': ['hostid', 'host', 'name', 'status'],
            'filter': {'host': host_name},
            'selectInterfaces': ['ip']
        })['result']
        
        if not hosts:
            # Tentar buscar pelo nome visível
            hosts = self.api.do_request('host.get', {
                'output': ['hostid', 'host', 'name', 'status'],
                'filter': {'name': host_name},
                'selectInterfaces': ['ip']
            })['result']
        
        if hosts:
            return hosts[0]
        return {}
    
    def get_host_items(self, host_id: str) -> List[Dict[str, Any]]:
        """
        Obtém todos os itens de monitoramento de um host.
        
        Args:
            host_id: ID do host
            
        Returns:
            Lista de itens de monitoramento
        """
        return self.api.do_request('item.get', {
            'output': ['itemid', 'name', 'key_', 'lastvalue', 'lastclock', 'units'],
            'hostids': host_id,
            'sortfield': 'name'
        })['result']
    
    def get_problems(self, severity: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Obtém problemas ativos no Zabbix.
        
        Args:
            severity: Lista de níveis de severidade (opcional)
            
        Returns:
            Lista de problemas ativos
        """
        params = {
            'output': ['eventid', 'objectid', 'name', 'severity', 'clock', 'r_eventid'],
            'selectHosts': ['hostid', 'name'],
            'recent': True,
            'sortfield': ['clock', 'eventid'],
            'sortorder': 'DESC'
        }
        
        if severity:
            params['severities'] = severity
        
        return self.api.do_request('problem.get', params)['result']
    
    def get_history(self, 
                    item_id: str, 
                    history_type: int, 
                    time_from: Optional[int] = None,
                    time_till: Optional[int] = None,
                    limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtém o histórico de valores para um item específico.
        
        Args:
            item_id: ID do item
            history_type: Tipo de histórico (0-float, 1-string, 2-log, 3-integer, 4-text)
            time_from: Timestamp de início (opcional)
            time_till: Timestamp de fim (opcional)
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de valores históricos
        """
        params = {
            'output': 'extend',
            'itemids': item_id,
            'history': history_type,
            'sortfield': 'clock',
            'sortorder': 'ASC'
        }
        
        if time_from:
            params['time_from'] = time_from
        
        if time_till:
            params['time_till'] = time_till
            
        if limit:
            params['limit'] = limit
        
        return self.api.do_request('history.get', params)['result']
    
    def get_hosts_with_high_cpu(self, threshold: float = 80.0, period: str = '1h') -> List[Dict[str, Any]]:
        """
        Obtém hosts com utilização de CPU acima do threshold especificado.
        
        Args:
            threshold: Limite percentual para considerar CPU alta
            period: Período de tempo para verificar ('1h', '3h', '6h', '12h', '24h', '7d')
            
        Returns:
            Lista de hosts com CPU alta
        """
        # Converter período em segundos
        period_dict = {
            '1h': 3600,
            '3h': 10800,
            '6h': 21600,
            '12h': 43200,
            '24h': 86400,
            '7d': 604800
        }
        
        seconds = period_dict.get(period, 3600)
        time_from = int(time.time()) - seconds
        
        # Obter todos os hosts
        hosts = self.get_hosts()
        result = []
        
        for host in hosts:
            host_id = host['hostid']
            
            # Buscar itens de CPU do host
            cpu_items = self.api.do_request('item.get', {
                'output': ['itemid', 'name', 'key_'],
                'hostids': host_id,
                'search': {'key_': 'cpu', 'name': 'CPU'},
                'searchWildcardsEnabled': True
            })['result']
            
            if not cpu_items:
                continue
            
            # Para cada item de CPU, verificar se está acima do threshold
            for item in cpu_items:
                item_id = item['itemid']
                history = self.get_history(item_id, 0, time_from)
                
                if not history:
                    continue
                
                # Verificar valores
                max_value = 0
                for record in history:
                    value = float(record['value'])
                    max_value = max(max_value, value)
                
                if max_value > threshold:
                    host_copy = host.copy()
                    host_copy['cpu_max'] = str(max_value)
                    host_copy['item_name'] = item['name']
                    result.append(host_copy)
                    break  # Já encontramos um item acima do threshold para este host
        
        return result
    
    def get_hosts_with_low_memory(self, threshold: float = 10.0, period: str = '1h') -> List[Dict[str, Any]]:
        """
        Obtém hosts com pouca memória disponível (abaixo do threshold).
        
        Args:
            threshold: Limite percentual de memória livre para considerar
            period: Período de tempo para verificar ('1h', '3h', '6h', '12h', '24h', '7d')
            
        Returns:
            Lista de hosts com pouca memória
        """
        # Converter período em segundos (similar ao método get_hosts_with_high_cpu)
        period_dict = {
            '1h': 3600,
            '3h': 10800,
            '6h': 21600,
            '12h': 43200,
            '24h': 86400,
            '7d': 604800
        }
        
        seconds = period_dict.get(period, 3600)
        time_from = int(time.time()) - seconds
        
        # Obter todos os hosts
        hosts = self.get_hosts()
        result = []
        
        for host in hosts:
            host_id = host['hostid']
            
            # Buscar itens de memória do host
            memory_items = self.api.do_request('item.get', {
                'output': ['itemid', 'name', 'key_'],
                'hostids': host_id,
                'search': {'key_': 'mem', 'name': 'memory'},
                'searchWildcardsEnabled': True
            })['result']
            
            if not memory_items:
                continue
            
            # Para cada item de memória, verificar se está abaixo do threshold
            for item in memory_items:
                item_id = item['itemid']
                history = self.get_history(item_id, 0, time_from)
                
                if not history:
                    continue
                
                # Verificar valores
                min_value = float('inf')
                for record in history:
                    value = float(record['value'])
                    min_value = min(min_value, value)
                
                if min_value < threshold:
                    host_copy = host.copy()
                    host_copy['memory_min'] = str(min_value)
                    host_copy['item_name'] = item['name']
                    result.append(host_copy)
                    break  # Já encontramos um item abaixo do threshold para este host
        
        return result
    
    def get_host_uptime(self, host_id: str) -> Dict[str, Any]:
        """
        Obtém o tempo de atividade (uptime) de um host.
        
        Args:
            host_id: ID do host
            
        Returns:
            Dicionário com uptime em segundos e formatado
        """
        # Buscar item de uptime
        uptime_items = self.api.do_request('item.get', {
            'output': ['itemid', 'name', 'lastvalue'],
            'hostids': host_id,
            'search': {'key_': 'uptime'},
            'searchWildcardsEnabled': True
        })['result']
        
        if not uptime_items:
            return {'uptime_seconds': 0, 'uptime_formatted': 'Indisponível'}
        
        # Usar o primeiro item de uptime encontrado
        uptime_seconds = int(float(uptime_items[0]['lastvalue']))
        
        # Formatar para exibição amigável
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_formatted = f"{days} dias, {hours} horas, {minutes} minutos"
        
        return {
            'uptime_seconds': uptime_seconds,
            'uptime_formatted': uptime_formatted,
            'item_name': uptime_items[0]['name']
        }
    
    def get_unavailable_services(self) -> List[Dict[str, Any]]:
        """
        Obtém serviços indisponíveis no momento.
        
        Returns:
            Lista de serviços indisponíveis com detalhes
        """
        # Obter triggers ativos relacionados a serviços
        triggers = self.api.do_request('trigger.get', {
            'output': ['triggerid', 'description', 'priority', 'lastchange'],
            'filter': {'value': 1},  # 1 = problema ativo
            'selectHosts': ['hostid', 'name'],
            'selectItems': ['itemid', 'name'],
            'search': {'description': 'service'},
            'searchWildcardsEnabled': True,
            'sortfield': 'lastchange',
            'sortorder': 'DESC'
        })['result']
        
        return triggers
    
    def generate_graph_data(self, 
                           item_id: str, 
                           period: str = '7d',
                           history_type: int = 0) -> Dict[str, Any]:
        """
        Gera dados para graficação de um item.
        
        Args:
            item_id: ID do item a ser graficado
            period: Período de tempo ('1h', '3h', '6h', '12h', '24h', '7d', '30d')
            history_type: Tipo de histórico (0-float, 1-string, 2-log, 3-integer, 4-text)
            
        Returns:
            Dicionário com timestamps e valores para gráfico
        """
        # Converter período em segundos
        period_dict = {
            '1h': 3600,
            '3h': 10800,
            '6h': 21600,
            '12h': 43200,
            '24h': 86400,
            '7d': 604800,
            '30d': 2592000
        }
        
        seconds = period_dict.get(period, 604800)  # Padrão: 7 dias
        time_from = int(time.time()) - seconds
        
        # Obter dados do item
        item_info = self.api.do_request('item.get', {
            'output': ['name', 'units', 'key_'],
            'itemids': item_id
        })['result']
        
        if not item_info:
            return {
                'timestamps': [],
                'values': [],
                'name': 'Item não encontrado',
                'units': ''
            }
        
        item_name = item_info[0]['name']
        units = item_info[0]['units']
        
        # Obter histórico
        history = self.get_history(item_id, history_type, time_from)
        
        # Processar dados
        timestamps = []
        values = []
        
        for record in history:
            timestamps.append(int(record['clock']) * 1000)  # Converter para milissegundos para JS
            values.append(float(record['value']))
        
        return {
            'timestamps': timestamps,
            'values': values,
            'name': item_name,
            'units': units
        }
    
    def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Executa uma consulta em linguagem natural no Zabbix.
        
        Args:
            query: Consulta em linguagem natural
            
        Returns:
            Resultado da consulta
        """
        query_lower = query.lower()
        
        # Processar diferentes tipos de consultas
        if "cpu" in query_lower and ("alta" in query_lower or "acima" in query_lower):
            # Extrair threshold e período, se especificados
            threshold = 80.0  # valor padrão
            period = '1h'     # período padrão
            
            # Tentar extrair threshold (por exemplo, "acima de 90%")
            import re
            threshold_match = re.search(r'acima de (\d+)%', query_lower)
            if threshold_match:
                threshold = float(threshold_match.group(1))
            
            # Tentar extrair período
            if "última hora" in query_lower:
                period = '1h'
            elif "últimas 3 horas" in query_lower:
                period = '3h'
            elif "últimas 6 horas" in query_lower:
                period = '6h'
            elif "últimas 12 horas" in query_lower:
                period = '12h'
            elif "último dia" in query_lower or "últimas 24 horas" in query_lower:
                period = '24h'
            elif "última semana" in query_lower or "últimos 7 dias" in query_lower:
                period = '7d'
            
            hosts = self.get_hosts_with_high_cpu(threshold, period)
            return {
                'type': 'hosts_with_high_cpu',
                'data': hosts,
                'threshold': threshold,
                'period': period
            }
        
        elif "memória" in query_lower and ("baixa" in query_lower or "abaixo" in query_lower):
            # Lógica similar à CPU, adaptada para memória baixa
            threshold = 10.0  # valor padrão
            period = '1h'     # período padrão
            
            # Processamento similar ao de CPU alta
            hosts = self.get_hosts_with_low_memory(threshold, period)
            return {
                'type': 'hosts_with_low_memory',
                'data': hosts,
                'threshold': threshold,
                'period': period
            }
        
        elif "uptime" in query_lower:
            # Extrair nome ou ID do host
            host_info = None
            
            # Buscar menção a qualquer host na consulta
            hosts = self.get_hosts()
            for host in hosts:
                if host['host'].lower() in query_lower or host['name'].lower() in query_lower:
                    host_info = self.get_host_uptime(host['hostid'])
                    host_info.update({
                        'host': host['host'],
                        'name': host['name']
                    })
                    break
            
            if not host_info:
                return {
                    'type': 'error',
                    'message': 'Host não especificado ou não encontrado.'
                }
            
            return {
                'type': 'host_uptime',
                'data': host_info
            }
        
        elif "serviços indisponíveis" in query_lower or "serviços fora do ar" in query_lower:
            services = self.get_unavailable_services()
            return {
                'type': 'unavailable_services',
                'data': services
            }
        
        elif "gráfico" in query_lower:
            # Extração de informações para gerar gráfico
            host_name = None
            item_name = None
            period = '7d'  # padrão: 7 dias
            
            # Tentar extrair nome do host e do item
            hosts = self.get_hosts()
            for host in hosts:
                if host['host'].lower() in query_lower or host['name'].lower() in query_lower:
                    host_name = host['host']
                    host_id = host['hostid']
                    break
            
            if not host_name:
                return {
                    'type': 'error',
                    'message': 'Host não especificado ou não encontrado.'
                }
            
            # Identificar o item para graficar
            if "cpu" in query_lower:
                search_term = "cpu"
            elif "memória" in query_lower or "ram" in query_lower:
                search_term = "memory"
            elif "disco" in query_lower:
                search_term = "disk"
            elif "rede" in query_lower or "tráfego" in query_lower:
                search_term = "network"
            else:
                search_term = None
            
            if not search_term:
                return {
                    'type': 'error',
                    'message': 'Tipo de item não especificado ou não reconhecido.'
                }
            
            # Buscar item do tipo especificado
            items = self.api.do_request('item.get', {
                'output': ['itemid', 'name', 'key_'],
                'hostids': host_id,
                'search': {'key_': search_term},
                'searchWildcardsEnabled': True
            })['result']
            
            if not items:
                return {
                    'type': 'error',
                    'message': f'Nenhum item de {search_term} encontrado para o host {host_name}.'
                }
            
            # Usar o primeiro item encontrado
            item_id = items[0]['itemid']
            
            # Extrair período, se especificado
            if "última hora" in query_lower:
                period = '1h'
            elif "últimas 24 horas" in query_lower or "último dia" in query_lower:
                period = '24h'
            elif "últimos 7 dias" in query_lower or "última semana" in query_lower:
                period = '7d'
            elif "últimos 30 dias" in query_lower or "último mês" in query_lower:
                period = '30d'
            
            # Gerar dados para o gráfico
            graph_data = self.generate_graph_data(item_id, period)
            graph_data['host'] = host_name
            
            return {
                'type': 'graph',
                'data': graph_data,
                'period': period
            }
        
        else:
            # Consulta não reconhecida
            return {
                'type': 'error',
                'message': 'Não foi possível entender sua consulta. Por favor, reformule-a.'
            }
    
    def close(self):
        """Fecha a conexão com a API do Zabbix."""
        self.api.logout()

# Criar instância singleton do serviço
_zabbix_service = None

def get_zabbix_service():
    """
    Obtém uma instância única do serviço Zabbix.
    Implementa o padrão Singleton para evitar múltiplas conexões.
    
    Returns:
        Instância do serviço ZabbixService
    """
    global _zabbix_service
    
    if _zabbix_service is None:
        # Obter credenciais das configurações
        url = settings.ZABBIX_URL
        username = settings.ZABBIX_USERNAME
        password = settings.ZABBIX_PASSWORD
        
        _zabbix_service = ZabbixService(url, username, password)
    
    return _zabbix_service 