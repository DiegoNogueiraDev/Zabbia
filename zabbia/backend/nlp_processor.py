import logging
import re
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class QueryIntent:
    """Representa a intenção identificada em uma consulta"""
    HIGH_CPU = "high_cpu"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    HOST_STATUS = "host_status"
    HOST_UPTIME = "host_uptime"
    UNAVAILABLE_SERVICES = "unavailable_services"
    ALERT_SUMMARY = "alert_summary"
    GRAPH_REQUEST = "graph_request"
    HOST_MAINTENANCE = "host_maintenance"
    GENERAL_QUERY = "general_query"
    UNKNOWN = "unknown"

class TimeRange:
    """Representa um intervalo de tempo identificado em uma consulta"""
    def __init__(
        self, 
        from_timestamp: Optional[int] = None, 
        to_timestamp: Optional[int] = None,
        time_period: str = None
    ):
        self.from_timestamp = from_timestamp
        self.to_timestamp = to_timestamp
        self.time_period = time_period
    
    @classmethod
    def from_period(cls, period: str = "24h") -> 'TimeRange':
        """Cria um intervalo de tempo a partir de um período (ex: 1h, 24h, 7d)
        
        Args:
            period: String representando o período (ex: 1h, 24h, 7d)
            
        Returns:
            Instância de TimeRange
        """
        now = datetime.now()
        to_timestamp = int(now.timestamp())
        
        # Extrair número e unidade
        match = re.match(r"(\d+)([dhm])", period.lower())
        if not match:
            # Padrão: 24h
            from_timestamp = int((now - timedelta(hours=24)).timestamp())
            return cls(from_timestamp, to_timestamp, "24h")
        
        value = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'm':
            delta = timedelta(minutes=value)
            period_str = f"{value}m"
        elif unit == 'h':
            delta = timedelta(hours=value)
            period_str = f"{value}h"
        elif unit == 'd':
            delta = timedelta(days=value)
            period_str = f"{value}d"
        else:
            # Padrão para caso não reconhecido
            delta = timedelta(hours=24)
            period_str = "24h"
        
        from_timestamp = int((now - delta).timestamp())
        return cls(from_timestamp, to_timestamp, period_str)

class NLPProcessor:
    """Processador de linguagem natural para o Zabbia
    
    Esta classe é responsável por analisar consultas em linguagem natural
    e convertê-las em consultas SQL, chamadas de API ou ações específicas
    no Zabbix.
    """
    
    def __init__(self):
        """Inicializa o processador de linguagem natural"""
        # Padrões regex para identificação de intenções
        self.intent_patterns = {
            QueryIntent.HIGH_CPU: [
                r"(?:hosts?|servidore?s?).*(?:cpu|processador).*(?:alta|elevad[ao]|acima|maior)",
                r"cpu.*(?:acima|maior).*(?:\d+)[%\s]",
                r"quais? hosts? (?:est[áa][ão]o|com) cpu (?:alta|acima)"
            ],
            QueryIntent.MEMORY_USAGE: [
                r"(?:hosts?|servidore?s?).*(?:mem[óo]ria|ram).*(?:alta|elevad[ao]|acima|maior)",
                r"(?:mem[óo]ria|ram).*(?:acima|maior).*(?:\d+)[%\s]",
                r"uso de mem[óo]ria"
            ],
            QueryIntent.DISK_USAGE: [
                r"(?:hosts?|servidore?s?).*(?:disco|armazenamento|fs|filesystem).*(?:alta|elevad[ao]|acima|maior)",
                r"(?:disco|armazenamento).*(?:acima|maior).*(?:\d+)[%\s]",
                r"uso de disco"
            ],
            QueryIntent.HOST_STATUS: [
                r"status.*(?:hosts?|servidore?s?)",
                r"(?:hosts?|servidore?s?).*(?:status|estado)",
                r"quais? hosts? (?:est[áa][ão]o) (?:online|offline|down|up)"
            ],
            QueryIntent.HOST_UPTIME: [
                r"uptime.*(?:hosts?|servidore?s?)",
                r"(?:hosts?|servidore?s?).*uptime",
                r"(?:quanto tempo|desde quando).*(?:hosts?|servidore?s?).*(?:online|ativ[oa]s?)"
            ],
            QueryIntent.UNAVAILABLE_SERVICES: [
                r"(?:servi[çc]os?|aplica[çc][õo]es?).*(?:indispon[íi]ve(?:l|is)|offline|down|fora do ar)",
                r"quais?.*(?:servi[çc]os?|aplica[çc][õo]es?).*(?:est[áa][ão]o).*(?:indispon[íi]ve(?:l|is)|offline|down)"
            ],
            QueryIntent.ALERT_SUMMARY: [
                r"(?:resumo|sum[áa]rio).*(?:alerta|problema)s?",
                r"(?:alerta|problema)s?.*(?:resumo|sum[áa]rio)",
                r"(?:alertas|problemas).*(?:cr[íi]tico|grave)s?"
            ],
            QueryIntent.GRAPH_REQUEST: [
                r"(?:gr[áa]fico|chart).*(?:cpu|mem[óo]ria|ram|disco|rede|network)",
                r"(?:gerar?|criar?|mostrar?).*(?:gr[áa]fico|chart)",
                r"visualizar?.*(?:gr[áa]fico|chart)"
            ],
            QueryIntent.HOST_MAINTENANCE: [
                r"(?:colocar?|colocar?|por?|botar?).*(?:em manuten[çc][ãa]o|manutenir)",
                r"manuten[çc][ãa]o.*(?:hosts?|servidore?s?)",
                r"(?:hosts?|servidore?s?).*manuten[çc][ãa]o"
            ]
        }
        
        # Regex para extração de parâmetros
        self.host_pattern = r"(?:host|servidor[a]?|maquina)[:\s]+([a-zA-Z0-9\-_\.]+)"
        self.threshold_pattern = r"(?:acima|maior|superior|mais)[:\s]+(?:de|que)?[:\s]*(\d+)[%\s]"
        self.period_pattern = r"(?:últim(?:as?|os?))[:\s]+(\d+)[:\s]*(minutos?|horas?|dias?|m|h|d)"
        self.duration_pattern = r"(?:por|durante)[:\s]+(\d+)[:\s]*(minutos?|horas?|dias?|m|h|d)"
    
    def detect_intent(self, query: str) -> str:
        """Detecta a intenção da consulta
        
        Args:
            query: Consulta em linguagem natural
            
        Returns:
            Intenção da consulta (um dos valores de QueryIntent)
        """
        # Normalizar consulta (remover acentos, converter para minúsculas)
        normalized_query = query.lower()
        
        # Verificar cada padrão de intenção
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, normalized_query):
                    logger.debug(f"Intent detectada: {intent} para query '{query}'")
                    return intent
        
        # Se não encontrou uma intenção específica
        logger.debug(f"Intent não encontrada para query '{query}', usando general_query")
        return QueryIntent.GENERAL_QUERY
    
    def extract_host(self, query: str) -> Optional[str]:
        """Extrai o nome do host da consulta
        
        Args:
            query: Consulta em linguagem natural
            
        Returns:
            Nome do host ou None se não encontrado
        """
        match = re.search(self.host_pattern, query.lower())
        if match:
            return match.group(1)
        return None
    
    def extract_threshold(self, query: str, default: int = 80) -> int:
        """Extrai o valor de threshold da consulta
        
        Args:
            query: Consulta em linguagem natural
            default: Valor padrão se não encontrado
            
        Returns:
            Valor do threshold
        """
        match = re.search(self.threshold_pattern, query.lower())
        if match:
            return int(match.group(1))
        return default
    
    def extract_time_range(self, query: str) -> TimeRange:
        """Extrai o intervalo de tempo da consulta
        
        Args:
            query: Consulta em linguagem natural
            
        Returns:
            Objeto TimeRange
        """
        # Verificar período (últimas X horas, etc.)
        period_match = re.search(self.period_pattern, query.lower())
        if period_match:
            value = int(period_match.group(1))
            unit = period_match.group(2)[0].lower()  # Pegar primeira letra (m, h, d)
            
            if unit == 'm' or unit.startswith('m'):
                return TimeRange.from_period(f"{value}m")
            elif unit == 'h' or unit.startswith('h'):
                return TimeRange.from_period(f"{value}h")
            elif unit == 'd' or unit.startswith('d'):
                return TimeRange.from_period(f"{value}d")
        
        # Padrão: últimas 24 horas
        return TimeRange.from_period("24h")
    
    def extract_duration(self, query: str, default: int = 60) -> int:
        """Extrai a duração em minutos da consulta
        
        Args:
            query: Consulta em linguagem natural
            default: Valor padrão em minutos se não encontrado
            
        Returns:
            Duração em minutos
        """
        match = re.search(self.duration_pattern, query.lower())
        if match:
            value = int(match.group(1))
            unit = match.group(2)[0].lower()
            
            if unit == 'm' or unit.startswith('m'):
                return value
            elif unit == 'h' or unit.startswith('h'):
                return value * 60
            elif unit == 'd' or unit.startswith('d'):
                return value * 60 * 24
        
        return default
    
    def generate_sql(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Gera uma consulta SQL a partir da consulta em linguagem natural
        
        Args:
            query: Consulta em linguagem natural
            
        Returns:
            Tupla com (consulta SQL, parâmetros de contexto)
        """
        intent = self.detect_intent(query)
        context = {
            "intent": intent,
            "query": query
        }
        
        # Extrair parâmetros comuns
        host = self.extract_host(query)
        if host:
            context["host"] = host
        
        time_range = self.extract_time_range(query)
        context["time_range"] = time_range
        
        # Gerar SQL baseado na intenção
        if intent == QueryIntent.HIGH_CPU:
            threshold = self.extract_threshold(query, 80)
            context["threshold"] = threshold
            
            sql = """
            -- Hosts com CPU acima do threshold
            SELECT h.hostid, h.name,
                   100 - AVG(hu.value) AS cpu_usage
            FROM hosts h
            JOIN items i ON h.hostid = i.hostid
            JOIN history_uint hu ON i.itemid = hu.itemid
            WHERE i.key_ = 'system.cpu.util[,idle]'
              AND hu.clock > :from_time
              AND hu.clock <= :to_time
            """
            
            if host:
                sql += " AND h.name LIKE :host_pattern"
                context["host_pattern"] = f"%{host}%"
            
            sql += """
            GROUP BY h.hostid, h.name
            HAVING 100 - AVG(hu.value) > :threshold
            ORDER BY cpu_usage DESC;
            """
            
        elif intent == QueryIntent.MEMORY_USAGE:
            threshold = self.extract_threshold(query, 80)
            context["threshold"] = threshold
            
            sql = """
            -- Hosts com uso de memória acima do threshold
            SELECT h.hostid, h.name,
                   (1 - AVG(hm.value) / AVG(ht.value)) * 100 AS memory_usage
            FROM hosts h
            JOIN items im ON h.hostid = im.hostid
            JOIN items it ON h.hostid = it.hostid
            JOIN history hm ON im.itemid = hm.itemid
            JOIN history ht ON it.itemid = ht.itemid
            WHERE im.key_ = 'vm.memory.size[available]'
              AND it.key_ = 'vm.memory.size[total]'
              AND hm.clock > :from_time
              AND hm.clock <= :to_time
              AND ht.clock > :from_time
              AND ht.clock <= :to_time
            """
            
            if host:
                sql += " AND h.name LIKE :host_pattern"
                context["host_pattern"] = f"%{host}%"
            
            sql += """
            GROUP BY h.hostid, h.name
            HAVING (1 - AVG(hm.value) / AVG(ht.value)) * 100 > :threshold
            ORDER BY memory_usage DESC;
            """
            
        elif intent == QueryIntent.HOST_STATUS:
            sql = """
            -- Status dos hosts
            SELECT h.hostid, h.name,
                   CASE h.status
                       WHEN 0 THEN 'Enabled'
                       WHEN 1 THEN 'Disabled'
                       ELSE 'Unknown'
                   END AS status,
                   CASE h.available
                       WHEN 0 THEN 'Unknown'
                       WHEN 1 THEN 'Available'
                       WHEN 2 THEN 'Unavailable'
                       ELSE 'Unknown'
                   END AS availability
            FROM hosts h
            """
            
            if host:
                sql += " WHERE h.name LIKE :host_pattern"
                context["host_pattern"] = f"%{host}%"
            
            sql += " ORDER BY h.name;"
            
        elif intent == QueryIntent.HOST_UPTIME:
            sql = """
            -- Uptime dos hosts
            SELECT h.hostid, h.name,
                   hu.value AS uptime_seconds,
                   hu.value / 86400 AS uptime_days
            FROM hosts h
            JOIN items i ON h.hostid = i.hostid
            JOIN history_uint hu ON i.itemid = hu.itemid
            WHERE i.key_ = 'system.uptime'
              AND hu.clock > (UNIX_TIMESTAMP() - 300)
            """
            
            if host:
                sql += " AND h.name LIKE :host_pattern"
                context["host_pattern"] = f"%{host}%"
            
            sql += " ORDER BY h.name;"
        
        elif intent == QueryIntent.UNAVAILABLE_SERVICES:
            sql = """
            -- Serviços indisponíveis
            SELECT h.hostid, h.name AS host,
                   i.name AS service,
                   FROM_UNIXTIME(t.lastchange) AS since,
                   t.description AS problem
            FROM triggers t
            JOIN functions f ON t.triggerid = f.triggerid
            JOIN items i ON f.itemid = i.itemid
            JOIN hosts h ON i.hostid = h.hostid
            WHERE t.value = 1
              AND t.status = 0
              AND t.state = 0
            """
            
            if host:
                sql += " AND h.name LIKE :host_pattern"
                context["host_pattern"] = f"%{host}%"
            
            sql += " ORDER BY t.lastchange DESC;"
        
        elif intent == QueryIntent.ALERT_SUMMARY:
            sql = """
            -- Resumo de alertas
            SELECT p.eventid,
                   h.name AS host,
                   p.name AS problem,
                   p.severity,
                   FROM_UNIXTIME(p.clock) AS timestamp,
                   p.r_eventid IS NOT NULL AS resolved
            FROM problem p
            JOIN events e ON p.eventid = e.eventid
            JOIN triggers t ON e.objectid = t.triggerid
            JOIN functions f ON t.triggerid = f.triggerid
            JOIN items i ON f.itemid = i.itemid
            JOIN hosts h ON i.hostid = h.hostid
            WHERE p.clock > :from_time
              AND p.clock <= :to_time
            """
            
            if host:
                sql += " AND h.name LIKE :host_pattern"
                context["host_pattern"] = f"%{host}%"
            
            sql += " ORDER BY p.clock DESC;"
            
        else:
            # Consulta genérica
            sql = """
            -- Consulta genérica
            SELECT h.hostid, h.name, h.status, h.available
            FROM hosts h
            WHERE 1=1
            """
            
            if host:
                sql += " AND h.name LIKE :host_pattern"
                context["host_pattern"] = f"%{host}%"
            
            sql += " ORDER BY h.name;"
        
        return sql, context
    
    def generate_api_call(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Gera uma chamada de API a partir da consulta em linguagem natural
        
        Args:
            query: Consulta em linguagem natural
            
        Returns:
            Tupla com (método API, parâmetros)
        """
        intent = self.detect_intent(query)
        host = self.extract_host(query)
        time_range = self.extract_time_range(query)
        
        method = None
        params = {}
        
        if intent == QueryIntent.HOST_MAINTENANCE:
            method = "maintenance.create"
            host_ids = []  # Seria preenchido com IDs reais após busca
            duration = self.extract_duration(query, 60)  # Minutos
            
            params = {
                "name": f"Manutenção automática via Zabbia",
                "active_since": int(datetime.now().timestamp()),
                "active_till": int(datetime.now().timestamp() + duration * 60),
                "hostids": host_ids,
                "timeperiods": [
                    {
                        "timeperiod_type": 0,
                        "period": duration * 60
                    }
                ],
                "description": f"Manutenção criada via Zabbia em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "maintenance_type": 0  # 0 = com coleta de dados, 1 = sem coleta
            }
            
        elif intent == QueryIntent.HIGH_CPU:
            method = "item.get"
            threshold = self.extract_threshold(query, 80)
            
            params = {
                "output": ["itemid", "name", "lastvalue", "units"],
                "selectHosts": ["hostid", "name"],
                "search": {
                    "key_": "system.cpu.util"
                },
                "monitored": True
            }
            
            if host:
                params["host"] = host
                
        elif intent == QueryIntent.HOST_STATUS:
            method = "host.get"
            
            params = {
                "output": ["hostid", "name", "status", "available"],
                "selectInterfaces": ["ip", "type", "useip", "main"],
                "selectGroups": "extend"
            }
            
            if host:
                params["search"] = {"name": host}
                params["searchWildcardsEnabled"] = True
                
        elif intent == QueryIntent.UNAVAILABLE_SERVICES:
            method = "problem.get"
            
            params = {
                "output": "extend",
                "selectHosts": ["hostid", "name"],
                "recent": True,
                "sortfield": ["eventid"],
                "sortorder": "DESC"
            }
            
            if host:
                params["host"] = host
                
        return method, params
    
    def generate_graph_data(self, query: str) -> Dict[str, Any]:
        """Gera dados para um gráfico a partir da consulta em linguagem natural
        
        Args:
            query: Consulta em linguagem natural
            
        Returns:
            Dados para geração de gráfico (formato chartjs)
        """
        intent = self.detect_intent(query)
        host = self.extract_host(query)
        time_range = self.extract_time_range(query)
        
        chart_data = {
            "chartType": "line",
            "labels": [],
            "datasets": []
        }
        
        # Em uma implementação real, os dados seriam obtidos do banco
        # Aqui apenas retornamos a estrutura
        
        if "cpu" in query.lower():
            chart_data["title"] = f"Uso de CPU" + (f" - {host}" if host else "")
            chart_data["datasets"].append({
                "label": "CPU %",
                "data": [],
                "color": "#1f77b4",
                "fill": False
            })
            
        elif "memória" in query.lower() or "ram" in query.lower():
            chart_data["title"] = f"Uso de Memória" + (f" - {host}" if host else "")
            chart_data["datasets"].append({
                "label": "Memória %",
                "data": [],
                "color": "#ff7f0e",
                "fill": False
            })
            
        elif "disco" in query.lower():
            chart_data["title"] = f"Uso de Disco" + (f" - {host}" if host else "")
            chart_data["datasets"].append({
                "label": "Disco %",
                "data": [],
                "color": "#2ca02c",
                "fill": False
            })
            
        return chart_data

# Criar instância global do processador
nlp_processor = NLPProcessor() 