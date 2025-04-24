import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

from zabbia.backend.config import settings

logger = logging.getLogger(__name__)

class ZabbixAPIException(Exception):
    """Exceção específica para erros da API do Zabbix"""
    pass

class ZabbixAPIClient:
    """Cliente para interação com a API JSON-RPC do Zabbix
    
    Esta classe fornece métodos para acessar a API do Zabbix e executar
    operações como obter hosts, itens, eventos, histórico, etc.
    """
    
    def __init__(
        self, 
        api_url: str = None, 
        username: str = None, 
        password: str = None,
        api_token: Optional[str] = None,
        api_version: str = None
    ):
        """Inicializa o cliente da API Zabbix
        
        Args:
            api_url: URL da API Zabbix (opcional, padrão da configuração)
            username: Nome de usuário (opcional, padrão da configuração)
            password: Senha (opcional, padrão da configuração)
            api_token: Token de API (opcional, alternativa a username/password)
            api_version: Versão da API do Zabbix (ex: 6.0)
        """
        self.api_url = api_url or settings.zabbix_url
        self.username = username or settings.zabbix_username
        self.password = password or settings.zabbix_password
        self.api_token = api_token
        self.api_version = api_version or settings.api_version
        self.auth_token = None
        self.session = requests.Session()
        
        # Cabeçalhos padrão para requisições
        self.session.headers.update({
            'Content-Type': 'application/json',
        })
        
        # Se não foi fornecido um token de API, fazer login
        if not self.api_token:
            self.login()
    
    def login(self) -> bool:
        """Realiza login na API do Zabbix e obtém token de autenticação
        
        Returns:
            True se o login foi bem-sucedido, False caso contrário
        """
        try:
            # Preparar payload para autenticação
            payload = {
                "jsonrpc": "2.0",
                "method": "user.login",
                "params": {
                    "user": self.username,
                    "password": self.password
                },
                "id": 1
            }
            
            # Fazer requisição de login
            response = self.session.post(self.api_url, data=json.dumps(payload))
            response_data = response.json()
            
            # Verificar erro na resposta
            if "error" in response_data:
                error_msg = response_data["error"]["message"]
                error_data = response_data["error"]["data"]
                logger.error(f"Erro ao fazer login na API Zabbix: {error_msg} - {error_data}")
                return False
            
            # Armazenar token de autenticação
            self.auth_token = response_data["result"]
            logger.info("Login na API Zabbix realizado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Exceção ao fazer login na API Zabbix: {str(e)}")
            return False
    
    def api_call(self, method: str, params: Dict = None) -> Dict:
        """Executa uma chamada à API do Zabbix
        
        Args:
            method: Método da API a ser chamado (ex: 'host.get')
            params: Parâmetros para o método
            
        Returns:
            Resultado da chamada da API
            
        Raises:
            ZabbixAPIException: Em caso de erro na chamada da API
        """
        try:
            # Se não temos token de autenticação e não é método de login, tentar login
            if not self.auth_token and method != "user.login":
                success = self.login()
                if not success:
                    raise ZabbixAPIException("Não foi possível autenticar na API Zabbix")
            
            # Preparar payload para requisição
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or {},
                "id": 2
            }
            
            # Adicionar token de autenticação (exceto para login)
            if method != "user.login" and self.auth_token:
                payload["auth"] = self.auth_token
            
            # Fazer requisição
            response = self.session.post(self.api_url, data=json.dumps(payload))
            response_data = response.json()
            
            # Verificar erro na resposta
            if "error" in response_data:
                error_msg = response_data["error"]["message"]
                error_data = response_data["error"]["data"]
                logger.error(f"Erro ao chamar '{method}': {error_msg} - {error_data}")
                raise ZabbixAPIException(f"Erro na API Zabbix: {error_msg} - {error_data}")
            
            # Retornar resultado
            return response_data["result"]
            
        except ZabbixAPIException:
            # Repassar exceção específica
            raise
        except Exception as e:
            logger.error(f"Exceção ao chamar API Zabbix (método {method}): {str(e)}")
            raise ZabbixAPIException(f"Falha ao executar {method}: {str(e)}")
    
    def get_hosts(self, filter_data: Dict = None) -> List[Dict]:
        """Obtém lista de hosts do Zabbix
        
        Args:
            filter_data: Filtros opcionais para a busca de hosts
            
        Returns:
            Lista de hosts
        """
        params = {
            "output": "extend",
            "selectInterfaces": ["ip", "dns", "useip", "port", "type"],
            "selectGroups": "extend",
            "selectTags": "extend",
            "selectInventory": True,
            "sortfield": "name"
        }
        
        # Adicionar filtros se fornecidos
        if filter_data:
            params.update(filter_data)
        
        return self.api_call("host.get", params)
    
    def get_host_groups(self) -> List[Dict]:
        """Obtém grupos de hosts do Zabbix
        
        Returns:
            Lista de grupos de hosts
        """
        params = {
            "output": "extend",
            "sortfield": "name"
        }
        
        return self.api_call("hostgroup.get", params)
    
    def get_items(self, hostids: Union[List[str], str] = None, key_: str = None) -> List[Dict]:
        """Obtém itens do Zabbix
        
        Args:
            hostids: ID(s) do(s) host(s) para filtrar itens
            key_: Padrão de chave de item para filtrar
            
        Returns:
            Lista de itens
        """
        params = {
            "output": "extend",
            "sortfield": "name",
            "selectHosts": ["hostid", "name"],
            "monitored": True
        }
        
        # Adicionar filtro por host
        if hostids:
            if isinstance(hostids, str):
                hostids = [hostids]
            params["hostids"] = hostids
        
        # Adicionar filtro por key
        if key_:
            params["search"] = {"key_": key_}
            params["searchWildcardsEnabled"] = True
        
        return self.api_call("item.get", params)
    
    def get_problems(self, severity_from: int = None, severity_till: int = None) -> List[Dict]:
        """Obtém problemas ativos do Zabbix
        
        Args:
            severity_from: Severidade mínima dos problemas (0-5)
            severity_till: Severidade máxima dos problemas (0-5)
            
        Returns:
            Lista de problemas ativos
        """
        params = {
            "output": "extend",
            "selectHosts": ["hostid", "name"],
            "selectTags": "extend",
            "recent": True,
            "sortfield": ["eventid"],
            "sortorder": "DESC"
        }
        
        # Adicionar filtro por severidade
        if severity_from is not None or severity_till is not None:
            params["severities"] = []
            
            min_sev = severity_from if severity_from is not None else 0
            max_sev = severity_till if severity_till is not None else 5
            
            for sev in range(min_sev, max_sev + 1):
                params["severities"].append(sev)
        
        return self.api_call("problem.get", params)
    
    def get_triggers(self, hostids: Union[List[str], str] = None, active: bool = True) -> List[Dict]:
        """Obtém triggers do Zabbix
        
        Args:
            hostids: ID(s) do(s) host(s) para filtrar triggers
            active: Se True, retorna apenas triggers ativos
            
        Returns:
            Lista de triggers
        """
        params = {
            "output": "extend",
            "selectHosts": ["hostid", "name"],
            "selectDependencies": "extend",
            "expandDescription": True,
            "sortfield": "description"
        }
        
        # Adicionar filtro por host
        if hostids:
            if isinstance(hostids, str):
                hostids = [hostids]
            params["hostids"] = hostids
        
        # Adicionar filtro por status
        if active:
            params["filter"] = {"status": 0}  # 0 = enabled
        
        return self.api_call("trigger.get", params)
    
    def get_history(
        self, 
        itemids: Union[List[str], str],
        time_from: int = None,
        time_till: int = None,
        limit: int = 1000
    ) -> List[Dict]:
        """Obtém histórico de valores de itens
        
        Args:
            itemids: ID(s) do(s) item(ns) para obter histórico
            time_from: Timestamp de início para o histórico
            time_till: Timestamp de fim para o histórico
            limit: Limite de registros a retornar
            
        Returns:
            Lista de valores históricos
        """
        # Determinar o tipo do item para saber qual tabela de histórico consultar
        if isinstance(itemids, str):
            itemids = [itemids]
            
        # Primeiro, obter informações sobre os itens para determinar o tipo
        items = self.api_call("item.get", {
            "output": ["itemid", "value_type"],
            "itemids": itemids
        })
        
        if not items:
            return []
            
        # Agrupar itens por tipo
        items_by_type = {}
        for item in items:
            value_type = item["value_type"]
            if value_type not in items_by_type:
                items_by_type[value_type] = []
            items_by_type[value_type].append(item["itemid"])
        
        # Buscar histórico para cada tipo de item
        result = []
        for value_type, type_itemids in items_by_type.items():
            params = {
                "output": "extend",
                "itemids": type_itemids,
                "sortfield": "clock",
                "sortorder": "DESC",
                "limit": limit,
                "history": value_type
            }
            
            if time_from:
                params["time_from"] = time_from
                
            if time_till:
                params["time_till"] = time_till
            
            history = self.api_call("history.get", params)
            result.extend(history)
        
        return result
    
    def get_host_by_name(self, hostname: str) -> Optional[Dict]:
        """Obtém um host pelo nome
        
        Args:
            hostname: Nome ou padrão de nome do host
            
        Returns:
            Dados do host encontrado ou None
        """
        params = {
            "output": "extend",
            "selectInterfaces": "extend",
            "selectGroups": "extend",
            "selectInventory": True,
            "searchWildcardsEnabled": True,
            "search": {"name": hostname}
        }
        
        hosts = self.api_call("host.get", params)
        
        if hosts:
            return hosts[0]
        return None
    
    def get_graphs(self, hostids: Union[List[str], str] = None) -> List[Dict]:
        """Obtém gráficos do Zabbix
        
        Args:
            hostids: ID(s) do(s) host(s) para filtrar gráficos
            
        Returns:
            Lista de gráficos
        """
        params = {
            "output": "extend",
            "selectGraphItems": "extend",
            "sortfield": "name"
        }
        
        # Adicionar filtro por host
        if hostids:
            if isinstance(hostids, str):
                hostids = [hostids]
            params["hostids"] = hostids
        
        return self.api_call("graph.get", params)
    
    def acknowledge_event(
        self, 
        eventids: Union[List[str], str], 
        message: str = "Reconhecido via Zabbia",
        action: int = 6  # Reconhecer + Adicionar mensagem
    ) -> bool:
        """Reconhece um evento do Zabbix
        
        Args:
            eventids: ID(s) do(s) evento(s) a reconhecer
            message: Mensagem de reconhecimento
            action: Código da ação (6 = reconhecer + adicionar mensagem)
            
        Returns:
            True se a operação foi bem-sucedida
        """
        if isinstance(eventids, str):
            eventids = [eventids]
            
        params = {
            "eventids": eventids,
            "action": action,
            "message": message
        }
        
        try:
            self.api_call("event.acknowledge", params)
            return True
        except ZabbixAPIException:
            return False
    
    def create_host(
        self, 
        host: str, 
        visible_name: str,
        interfaces: List[Dict],
        group_ids: List[str], 
        templates: List[str] = None
    ) -> Optional[str]:
        """Cria um novo host no Zabbix
        
        Args:
            host: Nome técnico do host
            visible_name: Nome visível do host
            interfaces: Lista de interfaces (IP, porta, tipo)
            group_ids: IDs dos grupos de hosts
            templates: IDs dos templates a aplicar
            
        Returns:
            ID do host criado ou None em caso de falha
        """
        params = {
            "host": host,
            "name": visible_name,
            "interfaces": interfaces,
            "groups": [{"groupid": gid} for gid in group_ids]
        }
        
        if templates:
            params["templates"] = [{"templateid": tid} for tid in templates]
        
        try:
            result = self.api_call("host.create", params)
            return result["hostids"][0]
        except ZabbixAPIException:
            return None
            
    def update_host(self, hostid: str, **kwargs) -> bool:
        """Atualiza um host existente
        
        Args:
            hostid: ID do host a atualizar
            **kwargs: Campos a atualizar (status, nome, etc)
            
        Returns:
            True se a atualização foi bem-sucedida
        """
        params = {"hostid": hostid}
        params.update(kwargs)
        
        try:
            self.api_call("host.update", params)
            return True
        except ZabbixAPIException:
            return False
            
    def set_host_maintenance(
        self, 
        hostids: Union[List[str], str],
        name: str = "Manutenção via Zabbia",
        duration: int = 3600,  # 1 hora por padrão
        type_: int = 0  # 0 = com coleta de dados, 1 = sem coleta
    ) -> Optional[str]:
        """Coloca hosts em modo de manutenção
        
        Args:
            hostids: ID(s) do(s) host(s) para manutenção
            name: Nome da manutenção
            duration: Duração em segundos
            type_: Tipo de manutenção (0 = com dados, 1 = sem dados)
            
        Returns:
            ID da manutenção criada ou None em caso de falha
        """
        if isinstance(hostids, str):
            hostids = [hostids]
            
        # Calcular timestamps de início e fim
        start_time = int(datetime.now().timestamp())
        end_time = start_time + duration
        
        params = {
            "name": name,
            "active_since": start_time,
            "active_till": end_time,
            "hostids": hostids,
            "timeperiods": [
                {
                    "timeperiod_type": 0,
                    "period": duration
                }
            ],
            "description": f"Manutenção criada via Zabbia em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "maintenance_type": type_
        }
        
        try:
            result = self.api_call("maintenance.create", params)
            return result["maintenanceids"][0]
        except ZabbixAPIException:
            return None
            
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Obtém dados resumidos para dashboard
        
        Returns:
            Dicionário com dados para o dashboard
        """
        # Buscar hosts ativos
        hosts = self.api_call("host.get", {
            "output": ["hostid", "name", "status"],
            "filter": {"status": 0}  # 0 = enabled
        })
        
        # Buscar problemas por severidade
        problems = self.api_call("problem.get", {
            "output": ["eventid", "severity"],
            "recent": True
        })
        
        # Contar problemas por severidade
        severity_counts = {
            "disaster": 0,
            "high": 0,
            "average": 0,
            "warning": 0,
            "info": 0,
            "not_classified": 0
        }
        
        for problem in problems:
            sev = int(problem["severity"])
            if sev == 5:
                severity_counts["disaster"] += 1
            elif sev == 4:
                severity_counts["high"] += 1
            elif sev == 3:
                severity_counts["average"] += 1
            elif sev == 2:
                severity_counts["warning"] += 1
            elif sev == 1:
                severity_counts["info"] += 1
            else:
                severity_counts["not_classified"] += 1
        
        return {
            "hosts_count": len(hosts),
            "problems_count": len(problems),
            "severity_counts": severity_counts
        }
        
    def close(self):
        """Encerra a sessão HTTP e limpa recursos"""
        self.session.close()

# Criar instância global do cliente
api_client = ZabbixAPIClient() 