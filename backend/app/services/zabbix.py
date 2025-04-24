import json
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from fastapi import Depends
from sqlmodel import Session, select
import os

from app.services.database import get_db
from app.domain.models import Settings, Host, Metric, Alert

class ZabbixService:
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session
        self._api_url = None
        self._auth_token = None
        self._credentials = None
        self._session = None
    
    async def _get_credentials(self) -> dict:
        """
        Recupera as credenciais do Zabbix armazenadas no banco de dados.
        """
        if self._credentials is not None:
            return self._credentials
        
        settings = self.session.exec(
            select(Settings).where(Settings.key == "zabbix")
        ).first()
        
        if not settings:
            raise ValueError("Credenciais do Zabbix não encontradas")
        
        self._credentials = json.loads(settings.value)
        self._api_url = f"{self._credentials['url']}/api_jsonrpc.php"
        
        return self._credentials
    
    async def _get_auth_token(self) -> str:
        """
        Obtém um token de autenticação para o Zabbix API.
        """
        if self._auth_token is not None:
            return self._auth_token
        
        credentials = await self._get_credentials()
        
        # Se um token de API já foi fornecido nas configurações, usar isso
        if credentials.get("api_token"):
            self._auth_token = credentials["api_token"]
            return self._auth_token
        
        # Caso contrário, fazer login para obter um token
        if self._session is None:
            self._session = aiohttp.ClientSession()
        
        payload = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "user": credentials["username"],
                "password": credentials["password"]
            },
            "id": 1
        }
        
        try:
            async with self._session.post(self._api_url, json=payload) as response:
                result = await response.json()
                if "error" in result:
                    raise ValueError(f"Erro ao autenticar com Zabbix API: {result['error']['message']}")
                
                self._auth_token = result["result"]
                return self._auth_token
        
        except Exception as e:
            raise ValueError(f"Falha na comunicação com Zabbix API: {str(e)}")
    
    async def _api_call(self, method: str, params: dict = None) -> dict:
        """
        Faz uma chamada para a API Zabbix.
        """
        if self._session is None:
            self._session = aiohttp.ClientSession()
        
        auth_token = await self._get_auth_token()
        
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "auth": auth_token,
            "id": 1
        }
        
        try:
            async with self._session.post(self._api_url, json=payload) as response:
                result = await response.json()
                if "error" in result:
                    raise ValueError(f"Erro na API Zabbix: {result['error']['message']}")
                
                return result["result"]
        
        except Exception as e:
            if isinstance(e, ValueError) and "Erro na API Zabbix" in str(e):
                raise e
            raise ValueError(f"Falha na comunicação com Zabbix API: {str(e)}")
    
    async def test_connection(self) -> bool:
        """
        Testa a conexão com o Zabbix API.
        """
        try:
            await self._get_auth_token()
            return True
        except Exception:
            return False
    
    async def get_active_hosts(self) -> List[dict]:
        """
        Retorna a lista de hosts ativos no Zabbix.
        """
        params = {
            "output": ["hostid", "host", "name", "status", "description"],
            "selectInterfaces": ["ip", "dns", "useip", "port", "type"],
            "filter": {
                "status": 0  # 0 = ativo, 1 = inativo
            }
        }
        
        hosts = await self._api_call("host.get", params)
        
        # Salvar hosts no banco de dados local para cache
        for host_data in hosts:
            host = Host(
                host_id=host_data["hostid"],
                name=host_data["name"],
                status=int(host_data["status"]),
                description=host_data.get("description", ""),
                ip=host_data["interfaces"][0]["ip"] if host_data.get("interfaces") else None,
                dns=host_data["interfaces"][0]["dns"] if host_data.get("interfaces") else None,
                metadata=host_data
            )
            
            existing = self.session.exec(
                select(Host).where(Host.host_id == host_data["hostid"])
            ).first()
            
            if existing:
                # Atualizar host existente
                existing.name = host.name
                existing.status = host.status
                existing.description = host.description
                existing.ip = host.ip
                existing.dns = host.dns
                existing.metadata = host.metadata
                existing.updated_at = datetime.utcnow()
            else:
                # Adicionar novo host
                self.session.add(host)
        
        self.session.commit()
        
        return hosts
    
    async def get_host_details(self, host_name_or_id: str) -> Optional[dict]:
        """
        Obtém detalhes de um host específico pelo nome ou ID.
        """
        # Tentar buscar por ID primeiro
        params = {
            "output": "extend",
            "selectInterfaces": "extend",
            "selectGroups": "extend",
            "selectParentTemplates": "extend",
            "filter": {}
        }
        
        # Verificar se é um ID ou nome
        if host_name_or_id.isdigit():
            params["filter"] = {"hostid": host_name_or_id}
        else:
            params["filter"] = {"host": host_name_or_id}
            # Adicionar busca por nome visível também
            params["searchByAny"] = True
            params["search"] = {"name": host_name_or_id}
        
        hosts = await self._api_call("host.get", params)
        
        if not hosts:
            return None
        
        return hosts[0]
    
    async def get_cpu_metrics(self, hours: int = 24) -> List[dict]:
        """
        Obtém métricas de CPU para todos os hosts.
        """
        # Obter itens de CPU (normalmente 'system.cpu.util')
        items = await self._api_call("item.get", {
            "output": ["itemid", "hostid", "name", "key_"],
            "search": {
                "key_": "system.cpu.util"
            },
            "searchWildcardsEnabled": True
        })
        
        if not items:
            return []
        
        # Obter valores históricos para esses itens
        item_ids = [item["itemid"] for item in items]
        time_from = int((datetime.now() - timedelta(hours=hours)).timestamp())
        
        history = await self._api_call("history.get", {
            "output": "extend",
            "itemids": item_ids,
            "time_from": time_from,
            "sortfield": "clock",
            "sortorder": "ASC"
        })
        
        # Agrupar dados por host
        host_to_item = {item["hostid"]: item["itemid"] for item in items}
        result = {}
        
        for entry in history:
            host_id = next((hid for hid, iid in host_to_item.items() if iid == entry["itemid"]), None)
            if not host_id:
                continue
            
            if host_id not in result:
                result[host_id] = []
            
            result[host_id].append({
                "timestamp": datetime.fromtimestamp(int(entry["clock"])).isoformat(),
                "value": float(entry["value"])
            })
        
        # Transformar em lista para retorno
        return [{"host_id": host_id, "data": data} for host_id, data in result.items()]
    
    async def get_memory_metrics(self, hours: int = 24) -> List[dict]:
        """
        Obtém métricas de memória para todos os hosts.
        """
        # Obter itens de memória (normalmente 'vm.memory.util')
        items = await self._api_call("item.get", {
            "output": ["itemid", "hostid", "name", "key_"],
            "search": {
                "key_": "vm.memory"
            },
            "searchWildcardsEnabled": True
        })
        
        if not items:
            return []
        
        # Obter valores históricos para esses itens
        item_ids = [item["itemid"] for item in items]
        time_from = int((datetime.now() - timedelta(hours=hours)).timestamp())
        
        history = await self._api_call("history.get", {
            "output": "extend",
            "itemids": item_ids,
            "time_from": time_from,
            "sortfield": "clock",
            "sortorder": "ASC"
        })
        
        # Agrupar dados por host
        host_to_item = {item["hostid"]: item["itemid"] for item in items}
        result = {}
        
        for entry in history:
            host_id = next((hid for hid, iid in host_to_item.items() if iid == entry["itemid"]), None)
            if not host_id:
                continue
            
            if host_id not in result:
                result[host_id] = []
            
            result[host_id].append({
                "timestamp": datetime.fromtimestamp(int(entry["clock"])).isoformat(),
                "value": float(entry["value"])
            })
        
        # Transformar em lista para retorno
        return [{"host_id": host_id, "data": data} for host_id, data in result.items()]
    
    async def get_availability_metrics(self, hours: int = 24) -> List[dict]:
        """
        Obtém métricas de disponibilidade para todos os hosts.
        """
        # Obter triggers relacionadas a disponibilidade
        triggers = await self._api_call("trigger.get", {
            "output": ["triggerid", "description", "value"],
            "filter": {
                "value": 1  # 1 = problema, 0 = ok
            },
            "selectHosts": ["hostid"],
            "lastChangeSince": int((datetime.now() - timedelta(hours=hours)).timestamp())
        })
        
        # Calcular disponibilidade por host
        host_availability = {}
        
        for trigger in triggers:
            if not trigger.get("hosts"):
                continue
            
            host_id = trigger["hosts"][0]["hostid"]
            
            if host_id not in host_availability:
                host_availability[host_id] = {
                    "total_downtime_seconds": 0,
                    "events": []
                }
            
            # Obter eventos relacionados a este trigger
            events = await self._api_call("event.get", {
                "output": "extend",
                "objectids": trigger["triggerid"],
                "time_from": int((datetime.now() - timedelta(hours=hours)).timestamp()),
                "sortfield": "clock",
                "sortorder": "ASC"
            })
            
            for event in events:
                host_availability[host_id]["events"].append({
                    "timestamp": datetime.fromtimestamp(int(event["clock"])).isoformat(),
                    "value": int(event["value"]),  # 0 = OK, 1 = PROBLEM
                    "name": trigger["description"],
                    "event_id": event["eventid"]
                })
        
        # Calcular disponibilidade (porcentagem)
        for host_id, data in host_availability.items():
            if data["events"]:
                # Calcular tempo total de indisponibilidade
                events = sorted(data["events"], key=lambda e: e["timestamp"])
                
                # Analisar eventos em pares (problema -> resolução)
                problem_time = None
                total_downtime = 0
                
                for event in events:
                    if event["value"] == 1 and problem_time is None:  # PROBLEM
                        problem_time = datetime.fromisoformat(event["timestamp"])
                    elif event["value"] == 0 and problem_time is not None:  # OK
                        resolved_time = datetime.fromisoformat(event["timestamp"])
                        downtime = (resolved_time - problem_time).total_seconds()
                        total_downtime += downtime
                        problem_time = None
                
                # Se houver um problema sem resolução, contar até agora
                if problem_time is not None:
                    downtime = (datetime.now() - problem_time).total_seconds()
                    total_downtime += downtime
                
                # Calcular disponibilidade
                total_period = hours * 3600
                availability_percent = 100 - (total_downtime / total_period * 100)
                
                data["availability_percent"] = round(availability_percent, 2)
                data["total_downtime_seconds"] = total_downtime
            else:
                data["availability_percent"] = 100.0
                data["total_downtime_seconds"] = 0
        
        # Transformar em lista para retorno
        return [{"host_id": host_id, "data": data} for host_id, data in host_availability.items()]
    
    async def get_average_uptime(self) -> float:
        """
        Calcula o uptime médio de todos os hosts.
        """
        availability = await self.get_availability_metrics(hours=24)
        
        if not availability:
            return 100.0  # Se não houver dados, considerar 100%
        
        total_availability = sum(host["data"].get("availability_percent", 100.0) for host in availability)
        return round(total_availability / len(availability), 2)
    
    async def get_hosts_in_alert(self) -> List[dict]:
        """
        Retorna hosts que estão atualmente em alerta (com problemas).
        """
        # Obter triggers ativos (problemas)
        triggers = await self._api_call("trigger.get", {
            "output": ["triggerid", "description", "priority", "lastchange"],
            "filter": {
                "value": 1  # 1 = problema, 0 = ok
            },
            "selectHosts": ["hostid", "name"],
            "sortfield": "priority",
            "sortorder": "DESC"
        })
        
        # Agrupar alertas por host
        hosts_with_alerts = {}
        
        for trigger in triggers:
            if not trigger.get("hosts"):
                continue
            
            host = trigger["hosts"][0]
            host_id = host["hostid"]
            
            if host_id not in hosts_with_alerts:
                hosts_with_alerts[host_id] = {
                    "host_id": host_id,
                    "name": host["name"],
                    "alerts": []
                }
            
            hosts_with_alerts[host_id]["alerts"].append({
                "name": trigger["description"],
                "priority": int(trigger["priority"]),
                "since": datetime.fromtimestamp(int(trigger["lastchange"])).isoformat()
            })
        
        # Transformar em lista para retorno
        return list(hosts_with_alerts.values())
    
    async def get_host_metrics(self, host_id: str, from_date: datetime, to_date: datetime) -> dict:
        """
        Obtém métricas detalhadas para um host específico em um período.
        """
        # Obter itens para o host
        items = await self._api_call("item.get", {
            "output": ["itemid", "name", "key_", "value_type", "units"],
            "hostids": host_id,
            "sortfield": "name"
        })
        
        if not items:
            return {"cpu": [], "memory": [], "disk": [], "network": []}
        
        # Categorizar itens
        cpu_items = [item for item in items if "cpu" in item["key_"].lower()]
        memory_items = [item for item in items if "memory" in item["key_"].lower() or "mem" in item["key_"].lower()]
        disk_items = [item for item in items if "disk" in item["key_"].lower() or "vfs.fs" in item["key_"].lower()]
        network_items = [item for item in items if "net" in item["key_"].lower() or "network" in item["key_"].lower()]
        
        # Obter histórico para cada categoria
        time_from = int(from_date.timestamp())
        time_till = int(to_date.timestamp())
        
        async def get_history_for_items(items_list):
            if not items_list:
                return []
            
            item_ids = [item["itemid"] for item in items_list]
            value_types = {item["itemid"]: item["value_type"] for item in items_list}
            units = {item["itemid"]: item["units"] for item in items_list}
            names = {item["itemid"]: item["name"] for item in items_list}
            
            results = []
            
            # Agrupar por tipo de valor para consultar o histórico correto
            for value_type in set(value_types.values()):
                type_item_ids = [itemid for itemid, vtype in value_types.items() if vtype == value_type]
                
                if not type_item_ids:
                    continue
                
                history = await self._api_call("history.get", {
                    "output": "extend",
                    "itemids": type_item_ids,
                    "time_from": time_from,
                    "time_till": time_till,
                    "sortfield": "clock",
                    "sortorder": "ASC",
                    "history": value_type
                })
                
                # Agrupar por item
                for entry in history:
                    item_id = entry["itemid"]
                    
                    results.append({
                        "name": names[item_id],
                        "timestamp": datetime.fromtimestamp(int(entry["clock"])).isoformat(),
                        "value": float(entry["value"]) if value_types[item_id] in [0, 3] else entry["value"],
                        "units": units[item_id]
                    })
            
            return results
        
        # Executar consultas em paralelo
        cpu_history, memory_history, disk_history, network_history = await asyncio.gather(
            get_history_for_items(cpu_items),
            get_history_for_items(memory_items),
            get_history_for_items(disk_items),
            get_history_for_items(network_items)
        )
        
        return {
            "cpu": cpu_history,
            "memory": memory_history,
            "disk": disk_history,
            "network": network_history
        }
    
    async def get_hosts_with_high_cpu(self, threshold: int = 80, period_minutes: int = 30) -> List[dict]:
        """
        Retorna hosts com uso de CPU acima do limite especificado.
        """
        # Obter itens de CPU
        items = await self._api_call("item.get", {
            "output": ["itemid", "hostid", "name", "key_"],
            "search": {
                "key_": "system.cpu.util"
            },
            "searchWildcardsEnabled": True
        })
        
        if not items:
            return []
        
        # Obter valores históricos recentes para esses itens
        item_ids = [item["itemid"] for item in items]
        time_from = int((datetime.now() - timedelta(minutes=period_minutes)).timestamp())
        
        history = await self._api_call("history.get", {
            "output": "extend",
            "itemids": item_ids,
            "time_from": time_from,
            "sortfield": "clock",
            "sortorder": "ASC"
        })
        
        # Calcular média de CPU por host
        host_cpu_avg = {}
        item_to_host = {item["itemid"]: item["hostid"] for item in items}
        
        for entry in history:
            item_id = entry["itemid"]
            host_id = item_to_host.get(item_id)
            
            if not host_id:
                continue
            
            if host_id not in host_cpu_avg:
                host_cpu_avg[host_id] = {"values": [], "avg": 0}
            
            # Para cálculo correto, verificar se é CPU idle ou utilização direta
            value = float(entry["value"])
            if "idle" in next((item["key_"] for item in items if item["itemid"] == item_id), ""):
                value = 100 - value  # Converter idle para utilização
            
            host_cpu_avg[host_id]["values"].append(value)
        
        # Calcular médias
        for host_id, data in host_cpu_avg.items():
            if data["values"]:
                data["avg"] = sum(data["values"]) / len(data["values"])
        
        # Filtrar hosts acima do threshold
        high_cpu_hosts = {}
        
        for host_id, data in host_cpu_avg.items():
            if data["avg"] >= threshold:
                high_cpu_hosts[host_id] = data["avg"]
        
        if not high_cpu_hosts:
            return []
        
        # Obter detalhes dos hosts com alta CPU
        hosts = await self._api_call("host.get", {
            "output": ["hostid", "host", "name"],
            "hostids": list(high_cpu_hosts.keys())
        })
        
        # Adicionar valor de CPU aos hosts
        for host in hosts:
            host["cpu"] = round(high_cpu_hosts[host["hostid"]], 2)
        
        # Ordenar por CPU (maior para menor)
        hosts.sort(key=lambda h: h["cpu"], reverse=True)
        
        return hosts
    
    async def close(self):
        """
        Fecha a sessão HTTP quando o serviço não for mais necessário.
        """
        if self._session:
            await self._session.close()
            self._session = None

async def test_zabbix_connection(url: str, username: str, password: str, api_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Testa uma conexão com o Zabbix com as credenciais fornecidas.
    """
    session = aiohttp.ClientSession()
    api_url = f"{url}/api_jsonrpc.php"
    
    try:
        # Se um token de API foi fornecido, testar diretamente
        if api_token:
            payload = {
                "jsonrpc": "2.0",
                "method": "apiinfo.version",
                "params": {},
                "auth": api_token,
                "id": 1
            }
            
            async with session.post(api_url, json=payload) as response:
                result = await response.json()
                if "error" in result:
                    return {"success": False, "error": result["error"]["message"]}
                
                return {"success": True, "version": result["result"]}
        
        # Caso contrário, tentar autenticar com usuário e senha
        else:
            payload = {
                "jsonrpc": "2.0",
                "method": "user.login",
                "params": {
                    "user": username,
                    "password": password
                },
                "id": 1
            }
            
            async with session.post(api_url, json=payload) as response:
                result = await response.json()
                if "error" in result:
                    return {"success": False, "error": result["error"]["message"]}
                
                # Verificar a versão usando o token obtido
                auth_token = result["result"]
                
                version_payload = {
                    "jsonrpc": "2.0",
                    "method": "apiinfo.version",
                    "params": {},
                    "auth": auth_token,
                    "id": 2
                }
                
                async with session.post(api_url, json=version_payload) as version_response:
                    version_result = await version_response.json()
                    
                    if "error" in version_result:
                        return {"success": False, "error": version_result["error"]["message"]}
                    
                    return {
                        "success": True,
                        "version": version_result["result"],
                        "auth_token": auth_token
                    }
    
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    finally:
        await session.close() 