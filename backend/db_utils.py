import logging
import mysql.connector
from typing import List, Dict, Any, Optional, Union, Tuple
from contextlib import contextmanager

from zabbia.backend.config import settings

logger = logging.getLogger(__name__)

class ZabbixDBClient:
    """Cliente para interação direta com o banco de dados do Zabbix
    
    Esta classe permite executar consultas SQL otimizadas diretamente no banco 
    do Zabbix, complementando a funcionalidade oferecida pela API REST.
    """
    
    def __init__(
        self,
        host: str = settings.zabbix_db_host,
        port: int = settings.zabbix_db_port,
        user: str = settings.zabbix_db_user,
        password: str = settings.zabbix_db_password,
        database: str = settings.zabbix_db_name,
    ):
        """Inicializa o cliente de banco de dados
        
        Args:
            host: Host do banco de dados
            port: Porta do banco de dados
            user: Usuário do banco de dados
            password: Senha do banco de dados
            database: Nome do banco de dados
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

    @contextmanager
    def get_connection(self):
        """Gerenciador de contexto para conexão com o banco de dados
        
        Yields:
            Conexão com o banco de dados do Zabbix
        """
        conn = None
        try:
            conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            yield conn
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            raise
        finally:
            if conn is not None:
                conn.close()
                
    def execute_query(
        self, 
        query: str, 
        params: Optional[Union[Dict[str, Any], List[Any], Tuple[Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Executa uma consulta SQL no banco de dados
        
        Args:
            query: Consulta SQL a ser executada
            params: Parâmetros para a consulta SQL (opcional)
            
        Returns:
            Lista de dicionários com os resultados da consulta
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                    
                result = cursor.fetchall()
                return result
            except Exception as e:
                logger.error(f"Erro ao executar consulta: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Params: {params}")
                raise
            finally:
                cursor.close()

    def execute_update(
        self, 
        query: str, 
        params: Optional[Union[Dict[str, Any], List[Any], Tuple[Any]]] = None
    ) -> int:
        """Executa uma consulta de atualização (INSERT, UPDATE, DELETE)
        
        Args:
            query: Consulta SQL a ser executada
            params: Parâmetros para a consulta SQL (opcional)
            
        Returns:
            Número de linhas afetadas
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                conn.commit()
                return cursor.rowcount
            except Exception as e:
                conn.rollback()
                logger.error(f"Erro ao executar atualização: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Params: {params}")
                raise
            finally:
                cursor.close()

    def get_hosts_with_issues(self, severity_min: int = 0) -> List[Dict[str, Any]]:
        """Obtém todos os hosts com problemas ativos
        
        Args:
            severity_min: Severidade mínima dos problemas (0-5)
            
        Returns:
            Lista de hosts com problemas ativos
        """
        query = """
        SELECT 
            h.hostid, 
            h.name AS host_name, 
            h.status,
            COUNT(p.eventid) AS problem_count,
            MAX(p.severity) AS max_severity
        FROM 
            hosts h
        JOIN 
            problem p ON p.objectid IN (
                SELECT t.triggerid 
                FROM triggers t 
                JOIN functions f ON t.triggerid = f.triggerid 
                JOIN items i ON f.itemid = i.itemid 
                WHERE i.hostid = h.hostid
            )
        WHERE 
            p.r_eventid IS NULL
            AND p.severity >= %s
            AND h.status = 0
        GROUP BY 
            h.hostid, h.name, h.status
        ORDER BY 
            max_severity DESC, problem_count DESC;
        """
        return self.execute_query(query, (severity_min,))

    def get_cpu_usage_by_host(self, cpu_threshold: float = 80.0) -> List[Dict[str, Any]]:
        """Obtém hosts com uso de CPU acima do limite especificado
        
        Args:
            cpu_threshold: Limite de CPU em porcentagem (padrão: 80%)
            
        Returns:
            Lista de hosts com uso de CPU acima do limite
        """
        query = """
        SELECT 
            h.hostid, 
            h.name AS host_name, 
            i.itemid,
            i.name AS item_name,
            MAX(CAST(hd.value AS DECIMAL(18,2))) AS cpu_value
        FROM 
            hosts h
        JOIN 
            items i ON h.hostid = i.hostid
        JOIN 
            history_uint hd ON i.itemid = hd.itemid
        WHERE 
            i.key_ LIKE 'system.cpu.util%' 
            AND hd.clock > UNIX_TIMESTAMP(NOW() - INTERVAL 15 MINUTE)
            AND h.status = 0
        GROUP BY 
            h.hostid, h.name, i.itemid, i.name
        HAVING 
            cpu_value > %s
        ORDER BY 
            cpu_value DESC;
        """
        return self.execute_query(query, (cpu_threshold,))

    def get_memory_usage_by_host(self, memory_threshold: float = 80.0) -> List[Dict[str, Any]]:
        """Obtém hosts com uso de memória acima do limite especificado
        
        Args:
            memory_threshold: Limite de memória em porcentagem (padrão: 80%)
            
        Returns:
            Lista de hosts com uso de memória acima do limite
        """
        query = """
        SELECT 
            h.hostid, 
            h.name AS host_name, 
            i.itemid,
            i.name AS item_name,
            MAX(CAST(hd.value AS DECIMAL(18,2))) AS memory_value
        FROM 
            hosts h
        JOIN 
            items i ON h.hostid = i.hostid
        JOIN 
            history_uint hd ON i.itemid = hd.itemid
        WHERE 
            (i.key_ LIKE 'vm.memory.util%' OR i.key_ LIKE 'vm.memory.size[pused]')
            AND hd.clock > UNIX_TIMESTAMP(NOW() - INTERVAL 15 MINUTE)
            AND h.status = 0
        GROUP BY 
            h.hostid, h.name, i.itemid, i.name
        HAVING 
            memory_value > %s
        ORDER BY 
            memory_value DESC;
        """
        return self.execute_query(query, (memory_threshold,))

    def get_disk_usage_by_host(self, disk_threshold: float = 80.0) -> List[Dict[str, Any]]:
        """Obtém hosts com uso de disco acima do limite especificado
        
        Args:
            disk_threshold: Limite de disco em porcentagem (padrão: 80%)
            
        Returns:
            Lista de hosts com uso de disco acima do limite
        """
        query = """
        SELECT 
            h.hostid, 
            h.name AS host_name, 
            i.itemid,
            i.name AS item_name,
            MAX(CAST(hd.value AS DECIMAL(18,2))) AS disk_value,
            i.key_ AS filesystem
        FROM 
            hosts h
        JOIN 
            items i ON h.hostid = i.hostid
        JOIN 
            history_uint hd ON i.itemid = hd.itemid
        WHERE 
            i.key_ LIKE 'vfs.fs.size%pused%' 
            AND hd.clock > UNIX_TIMESTAMP(NOW() - INTERVAL 30 MINUTE)
            AND h.status = 0
        GROUP BY 
            h.hostid, h.name, i.itemid, i.name, i.key_
        HAVING 
            disk_value > %s
        ORDER BY 
            disk_value DESC;
        """
        return self.execute_query(query, (disk_threshold,))

    def get_uptime_by_host(self, host_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtém o uptime dos hosts
        
        Args:
            host_name: Nome do host específico (opcional)
            
        Returns:
            Lista com o uptime dos hosts
        """
        params = []
        query = """
        SELECT 
            h.hostid, 
            h.name AS host_name, 
            i.itemid,
            i.name AS item_name,
            hd.value AS uptime_seconds,
            hd.clock AS last_updated
        FROM 
            hosts h
        JOIN 
            items i ON h.hostid = i.hostid
        JOIN 
            history_uint hd ON i.itemid = hd.itemid
        WHERE 
            i.key_ LIKE 'system.uptime' 
            AND hd.clock = (
                SELECT MAX(clock) 
                FROM history_uint 
                WHERE itemid = i.itemid
            )
        """
        
        if host_name:
            query += " AND h.name LIKE %s"
            params.append(f"%{host_name}%")
            
        query += """
        AND h.status = 0
        ORDER BY 
            h.name ASC;
        """
        
        return self.execute_query(query, params if params else None)

    def get_services_status(self, include_disabled: bool = False) -> List[Dict[str, Any]]:
        """Obtém o status dos serviços
        
        Args:
            include_disabled: Se True, inclui serviços desabilitados
            
        Returns:
            Lista com o status dos serviços
        """
        query = """
        SELECT 
            s.serviceid,
            s.name,
            s.status,
            s.algorithm,
            s.sortorder,
            s.weight,
            s.propagation_rule,
            s.propagation_value,
            s.description
        FROM 
            services s
        """
        
        if not include_disabled:
            query += " WHERE s.status = 0"
            
        query += " ORDER BY s.sortorder ASC, s.name ASC;"
        
        return self.execute_query(query)

    def get_last_items_data(
        self, 
        host_id: Optional[int] = None, 
        key_pattern: Optional[str] = None, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Obtém os últimos dados de itens
        
        Args:
            host_id: ID do host (opcional)
            key_pattern: Padrão para filtrar por chave de item (opcional)
            limit: Limite de resultados
            
        Returns:
            Lista com os últimos dados de itens
        """
        params = []
        query = """
        SELECT 
            h.hostid,
            h.name AS host_name,
            i.itemid,
            i.name AS item_name,
            i.key_,
            i.value_type,
            i.units,
            i.lastclock,
            i.lastvalue,
            i.status
        FROM 
            hosts h
        JOIN 
            items i ON h.hostid = i.hostid
        WHERE 
            h.status = 0
            AND i.status = 0
        """
        
        if host_id:
            query += " AND h.hostid = %s"
            params.append(host_id)
            
        if key_pattern:
            query += " AND i.key_ LIKE %s"
            params.append(f"%{key_pattern}%")
            
        query += f"""
        ORDER BY 
            i.lastclock DESC
        LIMIT {limit};
        """
        
        return self.execute_query(query, params if params else None)

    def get_item_history(
        self,
        item_id: int,
        time_from: Optional[int] = None,
        time_till: Optional[int] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Obtém o histórico de um item
        
        Args:
            item_id: ID do item
            time_from: Timestamp inicial (opcional)
            time_till: Timestamp final (opcional)
            limit: Limite de resultados
            
        Returns:
            Lista com o histórico do item
        """
        params = [item_id]
        
        # Busca o tipo de valor do item
        value_type_query = "SELECT value_type FROM items WHERE itemid = %s"
        value_type_result = self.execute_query(value_type_query, (item_id,))
        
        if not value_type_result:
            return []
            
        value_type = value_type_result[0]['value_type']
        
        # Seleciona a tabela correta com base no tipo de valor
        history_tables = {
            0: "history",         # float
            1: "history_str",     # string
            2: "history_log",     # log
            3: "history_uint",    # unsigned integer
            4: "history_text"     # text
        }
        
        if value_type not in history_tables:
            logger.error(f"Tipo de valor desconhecido: {value_type}")
            return []
            
        table_name = history_tables[value_type]
        
        query = f"""
        SELECT 
            itemid,
            clock,
            value,
            ns
        FROM 
            {table_name}
        WHERE 
            itemid = %s
        """
        
        if time_from:
            query += " AND clock >= %s"
            params.append(time_from)
            
        if time_till:
            query += " AND clock <= %s"
            params.append(time_till)
            
        query += f"""
        ORDER BY 
            clock DESC
        LIMIT {limit};
        """
        
        return self.execute_query(query, params)

# Instância global do cliente de banco de dados
db_client = ZabbixDBClient() 