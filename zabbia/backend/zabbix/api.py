import requests
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import time

from zabbia.backend.config import settings

logger = logging.getLogger(__name__)

class ZabbixAPI:
    """
    Classe para integração com a API do Zabbix.
    """
    
    def __init__(self, url: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        """
        Inicializa a conexão com a API do Zabbix.
        
        Args:
            url: URL da API do Zabbix (opcional, usa o valor das configurações por padrão)
            user: Nome de usuário (opcional, usa o valor das configurações por padrão)
            password: Senha (opcional, usa o valor das configurações por padrão)
        """
        self.url = url or settings.ZABBIX_URL
        self.user = user or settings.ZABBIX_USERNAME
        self.password = password or settings.ZABBIX_PASSWORD
        self.auth_token = None
        self.api_version = None
        self._session = requests.Session()
    
    def login(self) -> bool:
        """
        Realiza login na API do Zabbix e obtém o token de autenticação.
        
        Returns:
            True se o login for bem-sucedido, False caso contrário
        """
        try:
            response = self._api_call('user.login', {
                'user': self.user,
                'password': self.password
            }, auth_required=False)
            
            if response:
                self.auth_token = response
                # Obter versão da API
                self.api_version = self._get_api_version()
                logger.info(f"Login na API do Zabbix realizado com sucesso. Versão: {self.api_version}")
                return True
            else:
                logger.error("Falha ao obter token de autenticação")
                return False
        except Exception as e:
            logger.error(f"Erro ao realizar login na API do Zabbix: {e}")
            return False
    
    def _get_api_version(self) -> Optional[str]:
        """
        Obtém a versão da API do Zabbix.
        
        Returns:
            String com a versão da API ou None em caso de erro
        """
        try:
            response = self._api_call('apiinfo.version', {}, auth_required=False)
            return response
        except Exception as e:
            logger.error(f"Erro ao obter versão da API: {e}")
            return None
    
    def _api_call(self, method: str, params: Dict[str, Any], auth_required: bool = True) -> Any:
        """
        Realiza uma chamada à API do Zabbix.
        
        Args:
            method: Método da API a ser chamado
            params: Parâmetros da chamada
            auth_required: Se a chamada requer autenticação
            
        Returns:
            Resultado da chamada à API
            
        Raises:
            Exception: Se ocorrer um erro na chamada à API
        """
        request_id = int(time.time())
        request_data = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': request_id
        }
        
        if auth_required and self.auth_token:
            request_data['auth'] = self.auth_token
        
        try:
            response = self._session.post(
                self.url,
                data=json.dumps(request_data),
                headers={'Content-Type': 'application/json-rpc'},
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                error_message = f"Erro na API do Zabbix: {result['error'].get('message', 'Erro desconhecido')} - {result['error'].get('data', '')}"
                logger.error(error_message)
                raise Exception(error_message)
            
            return result.get('result')
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de requisição HTTP: {e}")
            raise Exception(f"Erro de comunicação com a API do Zabbix: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar resposta JSON: {e}")
            raise Exception(f"Resposta inválida da API do Zabbix: {e}")
        except Exception as e:
            logger.error(f"Erro na chamada à API do Zabbix: {e}")
            raise
    
    def logout(self) -> bool:
        """
        Realiza logout da API do Zabbix.
        
        Returns:
            True se o logout for bem-sucedido, False caso contrário
        """
        if not self.auth_token:
            return True
            
        try:
            self._api_call('user.logout', {})
            self.auth_token = None
            logger.info("Logout da API do Zabbix realizado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao realizar logout da API do Zabbix: {e}")
            return False
    
    def get_hosts(self, search: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Obtém a lista de hosts.
        
        Args:
            search: Parâmetros de busca (opcional)
            
        Returns:
            Lista de hosts
        """
        params = {
            'output': 'extend',
            'selectInterfaces': ['ip', 'dns', 'useip', 'type', 'port', 'available'],
            'selectGroups': ['groupid', 'name'],
            'selectParentTemplates': ['templateid', 'name']
        }
        
        if search:
            params['search'] = search
        
        try:
            return self._api_call('host.get', params) or []
        except Exception as e:
            logger.error(f"Erro ao obter hosts: {e}")
            return []
    
    def get_host_by_id(self, host_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações de um host específico pelo ID.
        
        Args:
            host_id: ID do host
            
        Returns:
            Dicionário com informações do host ou None se não encontrado
        """
        try:
            params = {
                'output': 'extend',
                'hostids': host_id,
                'selectInterfaces': ['ip', 'dns', 'useip', 'type', 'port', 'available'],
                'selectGroups': ['groupid', 'name'],
                'selectItems': ['itemid', 'name', 'key_', 'lastvalue', 'lastclock'],
                'selectTriggers': ['triggerid', 'description', 'priority', 'lastchange', 'value']
            }
            
            hosts = self._api_call('host.get', params) or []
            return hosts[0] if hosts else None
        except Exception as e:
            logger.error(f"Erro ao obter host {host_id}: {e}")
            return None
    
    def get_items(self, host_ids: Optional[List[str]] = None, 
                 item_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtém itens de monitoramento.
        
        Args:
            host_ids: Lista de IDs dos hosts (opcional)
            item_key: Chave do item para filtrar (opcional)
            
        Returns:
            Lista de itens
        """
        params = {
            'output': 'extend',
            'selectHosts': ['hostid', 'name'],
            'sortfield': 'name'
        }
        
        if host_ids:
            params['hostids'] = host_ids
        
        if item_key:
            params['search'] = {'key_': item_key}
        
        try:
            return self._api_call('item.get', params) or []
        except Exception as e:
            logger.error(f"Erro ao obter itens: {e}")
            return []
    
    def get_history(self, item_ids: List[str], 
                   history_type: int = 0,
                   time_from: Optional[int] = None,
                   time_till: Optional[int] = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtém o histórico de valores de itens.
        
        Args:
            item_ids: Lista de IDs dos itens
            history_type: Tipo de histórico (0 - float, 1 - string, 2 - log, 3 - integer, 4 - text)
            time_from: Timestamp de início (opcional)
            time_till: Timestamp de fim (opcional)
            limit: Limite de registros
            
        Returns:
            Lista com o histórico de valores
        """
        if not item_ids:
            return []
            
        # Se não forem especificados os timestamps, pega as últimas 24 horas
        if not time_from:
            time_from = int((datetime.now() - timedelta(days=1)).timestamp())
        
        if not time_till:
            time_till = int(datetime.now().timestamp())
        
        params = {
            'output': 'extend',
            'itemids': item_ids,
            'history': history_type,
            'sortfield': 'clock',
            'sortorder': 'DESC',
            'time_from': time_from,
            'time_till': time_till,
            'limit': limit
        }
        
        try:
            history = self._api_call('history.get', params) or []
            return history
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {e}")
            return []
    
    def get_problems(self, host_ids: Optional[List[str]] = None,
                    severity: Optional[List[int]] = None,
                    recent: bool = False) -> List[Dict[str, Any]]:
        """
        Obtém problemas ativos.
        
        Args:
            host_ids: Lista de IDs dos hosts (opcional)
            severity: Lista de níveis de severidade (opcional)
            recent: Se True, retorna apenas problemas das últimas 24 horas
            
        Returns:
            Lista de problemas
        """
        params = {
            'output': 'extend',
            'selectHosts': ['hostid', 'name'],
            'sortfield': ['eventid'],
            'sortorder': 'DESC'
        }
        
        if host_ids:
            params['hostids'] = host_ids
        
        if severity:
            params['severities'] = severity
        
        if recent:
            params['time_from'] = int((datetime.now() - timedelta(days=1)).timestamp())
        
        try:
            problems = self._api_call('problem.get', params) or []
            
            # Adicionar nome do host em cada problema para facilitar o processamento
            for problem in problems:
                if 'hosts' in problem and problem['hosts']:
                    problem['host'] = problem['hosts'][0]['name']
            
            return problems
        except Exception as e:
            logger.error(f"Erro ao obter problemas: {e}")
            return []
    
    def get_triggers(self, host_ids: Optional[List[str]] = None,
                    only_active: bool = False) -> List[Dict[str, Any]]:
        """
        Obtém triggers.
        
        Args:
            host_ids: Lista de IDs dos hosts (opcional)
            only_active: Se True, retorna apenas triggers ativos
            
        Returns:
            Lista de triggers
        """
        params = {
            'output': 'extend',
            'selectHosts': ['hostid', 'name'],
            'selectItems': ['itemid', 'name'],
            'sortfield': 'priority',
            'sortorder': 'DESC'
        }
        
        if host_ids:
            params['hostids'] = host_ids
        
        if only_active:
            params['filter'] = {'value': 1}  # 1 = problema, 0 = ok
        
        try:
            triggers = self._api_call('trigger.get', params) or []
            
            # Adicionar nome do host em cada trigger para facilitar o processamento
            for trigger in triggers:
                if 'hosts' in trigger and trigger['hosts']:
                    trigger['host'] = trigger['hosts'][0]['name']
            
            return triggers
        except Exception as e:
            logger.error(f"Erro ao obter triggers: {e}")
            return []
    
    def execute_custom_query(self, method: str, params: Dict[str, Any]) -> Any:
        """
        Executa uma consulta personalizada à API do Zabbix.
        
        Args:
            method: Método da API
            params: Parâmetros da consulta
            
        Returns:
            Resultado da consulta
        """
        try:
            return self._api_call(method, params)
        except Exception as e:
            logger.error(f"Erro ao executar consulta personalizada ({method}): {e}")
            return None 