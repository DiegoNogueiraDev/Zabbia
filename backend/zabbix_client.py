import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union
from requests.exceptions import RequestException

from zabbia.backend.config import settings

logger = logging.getLogger(__name__)

class ZabbixAPIException(Exception):
    """Exceção para erros na API do Zabbix"""
    pass

class ZabbixClient:
    """Cliente para interagir com a API do Zabbix"""
    
    def __init__(self, url: str = None, username: str = None, password: str = None):
        """Inicializa o cliente Zabbix com as credenciais
        
        Args:
            url: URL da API Zabbix (opcional, usa config)
            username: Usuário Zabbix (opcional, usa config)
            password: Senha Zabbix (opcional, usa config)
        """
        self.url = url or settings.zabbix_url
        self.username = username or settings.zabbix_username
        self.password = password or settings.zabbix_password
        self.auth_token = None
        self.api_version = None
        self.request_id = 1
    
    def login(self) -> bool:
        """Realiza autenticação na API do Zabbix
        
        Returns:
            bool: True se autenticação bem-sucedida
        
        Raises:
            ZabbixAPIException: Se ocorrer erro na autenticação
        """
        try:
            response = self._api_call("user.login", {
                "user": self.username,
                "password": self.password
            }, auth_required=False)
            
            self.auth_token = response
            self._get_api_version()
            logger.info(f"Autenticado na API Zabbix, versão {self.api_version}")
            return True
            
        except Exception as e:
            logger.error(f"Falha na autenticação Zabbix: {str(e)}")
            raise ZabbixAPIException(f"Erro na autenticação: {str(e)}")
    
    def _get_api_version(self) -> str:
        """Obtém a versão da API do Zabbix
        
        Returns:
            str: Versão da API
        """
        try:
            self.api_version = self._api_call("apiinfo.version", {}, auth_required=False)
            return self.api_version
        except Exception as e:
            logger.warning(f"Não foi possível obter a versão da API: {str(e)}")
            return "unknown"
    
    def _api_call(self, method: str, params: Dict[str, Any], auth_required: bool = True) -> Any:
        """Realiza chamada à API do Zabbix
        
        Args:
            method: Método da API Zabbix
            params: Parâmetros da chamada
            auth_required: Se requer autenticação
            
        Returns:
            Any: Resposta da API
            
        Raises:
            ZabbixAPIException: Se ocorrer erro na chamada
        """
        headers = {
            'Content-Type': 'application/json-rpc',
            'User-Agent': f'Zabbia/{settings.api_version}'
        }
        
        data = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': self.request_id,
        }
        
        if auth_required and self.auth_token:
            data['auth'] = self.auth_token
        
        self.request_id += 1
        
        try:
            logger.debug(f"Chamando método Zabbix: {method}")
            response = requests.post(self.url, data=json.dumps(data), headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            if 'error' in result:
                error_message = result['error']['message']
                error_data = result['error']['data']
                error = f"{error_message}: {error_data}"
                logger.error(f"Erro na API Zabbix: {error}")
                raise ZabbixAPIException(error)
                
            return result['result']
            
        except RequestException as e:
            logger.error(f"Erro na requisição à API Zabbix: {str(e)}")
            raise ZabbixAPIException(f"Erro na comunicação com API: {str(e)}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar resposta da API: {str(e)}")
            raise ZabbixAPIException(f"Erro ao processar resposta: {str(e)}")
            
        except Exception as e:
            logger.error(f"Erro inesperado na chamada Zabbix: {str(e)}")
            raise ZabbixAPIException(f"Erro na chamada: {str(e)}")
    
    def get_hosts(self, filter_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Obtém lista de hosts com filtros opcionais
        
        Args:
            filter_params: Parâmetros de filtro opcional
            
        Returns:
            List[Dict[str, Any]]: Lista de hosts
        """
        params = {
            "output": "extend",
            "selectInterfaces": ["interfaceid", "ip", "dns", "useip", "port", "type", "main"],
        }
        
        if filter_params:
            params.update(filter_params)
            
        return self._api_call("host.get", params)
        
    def get_items(self, hostids: Optional[Union[str, List[str]]] = None,
                  filter_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Obtém itens de monitoramento com filtros opcionais
        
        Args:
            hostids: ID do host ou lista de IDs
            filter_params: Parâmetros de filtro opcional
            
        Returns:
            List[Dict[str, Any]]: Lista de itens
        """
        params = {
            "output": "extend",
            "sortfield": "name"
        }
        
        if hostids:
            if isinstance(hostids, str):
                hostids = [hostids]
            params["hostids"] = hostids
            
        if filter_params:
            params.update(filter_params)
            
        return self._api_call("item.get", params)
        
    def get_history(self, itemids: Union[str, List[str]], history_type: int = 0,
                   time_from: Optional[int] = None, time_till: Optional[int] = None,
                   limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Obtém histórico de itens
        
        Args:
            itemids: ID do item ou lista de IDs
            history_type: Tipo de histórico (0 - float, 1 - str, 2 - log, 3 - int, 4 - text)
            time_from: Timestamp de início
            time_till: Timestamp de fim
            limit: Limite de registros
            
        Returns:
            List[Dict[str, Any]]: Histórico dos itens
        """
        if isinstance(itemids, str):
            itemids = [itemids]
            
        params = {
            "output": "extend",
            "history": history_type,
            "itemids": itemids,
            "sortfield": "clock",
            "sortorder": "DESC",
        }
        
        if time_from:
            params["time_from"] = time_from
            
        if time_till:
            params["time_till"] = time_till
            
        if limit:
            params["limit"] = limit
            
        return self._api_call("history.get", params)
        
    def get_problems(self, hostids: Optional[Union[str, List[str]]] = None,
                    filter_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Obtém problemas ativos
        
        Args:
            hostids: ID do host ou lista de IDs
            filter_params: Parâmetros de filtro opcional
            
        Returns:
            List[Dict[str, Any]]: Lista de problemas
        """
        params = {
            "output": "extend",
            "sortfield": ["eventid"],
            "sortorder": "DESC"
        }
        
        if hostids:
            if isinstance(hostids, str):
                hostids = [hostids]
            params["hostids"] = hostids
            
        if filter_params:
            params.update(filter_params)
            
        return self._api_call("problem.get", params)
        
    def get_triggers(self, hostids: Optional[Union[str, List[str]]] = None,
                    filter_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Obtém triggers com filtros opcionais
        
        Args:
            hostids: ID do host ou lista de IDs
            filter_params: Parâmetros de filtro opcional
            
        Returns:
            List[Dict[str, Any]]: Lista de triggers
        """
        params = {
            "output": "extend",
            "sortfield": "description"
        }
        
        if hostids:
            if isinstance(hostids, str):
                hostids = [hostids]
            params["hostids"] = hostids
            
        if filter_params:
            params.update(filter_params)
            
        return self._api_call("trigger.get", params)
        
    def get_host_groups(self) -> List[Dict[str, Any]]:
        """Obtém grupos de hosts
        
        Returns:
            List[Dict[str, Any]]: Lista de grupos de hosts
        """
        params = {
            "output": "extend"
        }
        
        return self._api_call("hostgroup.get", params)
        
    def logout(self) -> bool:
        """Encerra sessão na API do Zabbix
        
        Returns:
            bool: True se logout bem-sucedido
        """
        if not self.auth_token:
            return True
            
        try:
            result = self._api_call("user.logout", {})
            self.auth_token = None
            return bool(result)
        except Exception as e:
            logger.warning(f"Erro ao encerrar sessão Zabbix: {str(e)}")
            return False 