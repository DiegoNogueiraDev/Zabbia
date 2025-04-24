import logging
import mysql.connector
from typing import List, Dict, Any, Optional, Union
from contextlib import contextmanager

from zabbia.backend.config import settings

logger = logging.getLogger(__name__)

class ZabbixDBClient:
    """Cliente para consultas diretas ao banco de dados do Zabbix"""
    
    def __init__(
        self, 
        host: str = None, 
        port: int = None, 
        user: str = None, 
        password: str = None, 
        database: str = None
    ):
        """Inicializa o cliente de banco de dados do Zabbix
        
        Args:
            host: Host do banco de dados
            port: Porta do banco de dados
            user: Usuário do banco de dados
            password: Senha do banco de dados
            database: Nome do banco de dados
        """
        self.host = host or settings.db_host
        self.port = port or settings.db_port
        self.user = user or settings.db_user
        self.password = password or settings.db_password
        self.database = database or settings.db_name
        self.connection = None
        
    @contextmanager
    def get_connection(self):
        """Gerenciador de contexto para conexão com o banco de dados"""
        if not self.connection or not self.connection.is_connected():
            try:
                self.connection = mysql.connector.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database
                )
                logger.debug(f"Conexão estabelecida com o banco de dados {self.database}")
            except mysql.connector.Error as err:
                logger.error(f"Erro ao conectar ao banco de dados: {err}")
                raise
        
        try:
            yield self.connection
        except mysql.connector.Error as err:
            logger.error(f"Erro ao executar consulta: {err}")
            raise
        finally:
            pass  # Não fechamos a conexão aqui para reutilização
    
    def close(self):
        """Fecha a conexão com o banco de dados"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.debug("Conexão com o banco de dados fechada")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Executa uma consulta SQL e retorna os resultados
        
        Args:
            query: Consulta SQL
            params: Parâmetros para a consulta
            
        Returns:
            Lista de dicionários com os resultados
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                results = cursor.fetchall()
                return results
            finally:
                cursor.close()
    
    def execute_write_query(self, query: str, params: Optional[tuple] = None) -> int:
        """Executa uma consulta de escrita (INSERT, UPDATE, DELETE)
        
        Args:
            query: Consulta SQL
            params: Parâmetros para a consulta
            
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
            finally:
                cursor.close()
    
    # Consultas específicas para o Zabbix
    
    def get_host_performance(self, host_ids: Union[List[str], str], time_period: int = 3600) -> Dict[str, Any]:
        """Obtém dados de performance (CPU, memória, disco) para os hosts especificados
        
        Args:
            host_ids: ID ou lista de IDs de hosts
            time_period: Período de tempo em segundos (padrão: 1 hora)
            
        Returns:
            Dicionário com dados de performance por host
        """
        if isinstance(host_ids, str):
            host_ids = [host_ids]
            
        host_ids_str = ', '.join([f"'{h}'" for h in host_ids])
        
        # Consulta para obter itens de CPU, memória e disco
        query = f"""
        SELECT 
            h.host, 
            i.itemid, 
            i.name, 
            i.key_, 
            i.value_type,
            h.hostid
        FROM 
            hosts h
        JOIN 
            items i ON h.hostid = i.hostid
        WHERE 
            h.hostid IN ({host_ids_str})
            AND i.key_ IN (
                'system.cpu.util', 
                'vm.memory.util', 
                'vfs.fs.size[/,pused]'
            )
            AND i.status = 0  -- Item ativo
        """
        
        items = self.execute_query(query)
        
        # Para cada item, buscar valores históricos
        result = {}
        for item in items:
            host_name = item['host']
            item_id = item['itemid']
            item_name = item['name']
            item_key = item['key_']
            value_type = item['value_type']
            
            if host_name not in result:
                result[host_name] = {
                    'hostid': item['hostid'],
                    'cpu': [],
                    'memory': [],
                    'disk': []
                }
            
            # Determinar a tabela de histórico baseada no tipo de valor
            history_table = f'history_{value_type}'
            
            # Consulta para obter histórico
            history_query = f"""
            SELECT 
                clock, 
                value 
            FROM 
                {history_table} 
            WHERE 
                itemid = %s 
                AND clock > UNIX_TIMESTAMP() - %s
            ORDER BY 
                clock DESC
            """
            
            history_data = self.execute_query(history_query, (item_id, time_period))
            
            # Adicionar dados ao resultado
            if 'cpu' in item_key:
                result[host_name]['cpu'] = history_data
            elif 'memory' in item_key:
                result[host_name]['memory'] = history_data
            elif 'vfs.fs.size' in item_key:
                result[host_name]['disk'] = history_data
        
        return result
    
    def get_problems_count(self, severity_threshold: int = 0) -> int:
        """Retorna o número de problemas ativos com severidade maior ou igual ao threshold
        
        Args:
            severity_threshold: Limite mínimo de severidade (0-5)
            
        Returns:
            Número de problemas ativos
        """
        query = """
        SELECT 
            COUNT(*) as problem_count 
        FROM 
            problem p
        WHERE 
            p.severity >= %s
            AND p.r_eventid IS NULL  -- Problema não resolvido
        """
        
        result = self.execute_query(query, (severity_threshold,))
        return result[0]['problem_count'] if result else 0
    
    def get_top_hosts_by_problems(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna os hosts com mais problemas ativos
        
        Args:
            limit: Número máximo de hosts a retornar
            
        Returns:
            Lista de hosts com contagem de problemas
        """
        query = """
        SELECT 
            h.host, 
            h.name, 
            COUNT(p.eventid) as problem_count 
        FROM 
            hosts h
        JOIN 
            problem p ON p.objectid = h.hostid
        WHERE 
            p.source = 0  -- Trigger event
            AND p.object = 0  -- Host
            AND p.r_eventid IS NULL  -- Problema não resolvido
        GROUP BY 
            h.hostid
        ORDER BY 
            problem_count DESC
        LIMIT 
            %s
        """
        
        return self.execute_query(query, (limit,))
    
    def get_item_last_values(self, item_keys: List[str], host_pattern: str = None) -> List[Dict[str, Any]]:
        """Obtém os últimos valores para itens específicos
        
        Args:
            item_keys: Lista de chaves de itens (ex: system.cpu.util)
            host_pattern: Padrão para filtrar hosts (opcional)
            
        Returns:
            Lista com os últimos valores dos itens
        """
        keys_condition = ' OR '.join([f"i.key_ LIKE '%{key}%'" for key in item_keys])
        host_condition = f"AND h.host LIKE '%{host_pattern}%'" if host_pattern else ""
        
        query = f"""
        SELECT 
            h.host, 
            i.name as item_name, 
            i.key_, 
            i.value_type,
            i.itemid,
            i.lastvalue, 
            i.lastclock
        FROM 
            hosts h
        JOIN 
            items i ON h.hostid = i.hostid
        WHERE 
            ({keys_condition})
            {host_condition}
            AND i.status = 0  -- Item ativo
        ORDER BY 
            h.host, i.name
        """
        
        return self.execute_query(query)
    
    def generate_availability_report(self, period_days: int = 30) -> List[Dict[str, Any]]:
        """Gera relatório de disponibilidade dos hosts
        
        Args:
            period_days: Período em dias para o relatório
            
        Returns:
            Lista com dados de disponibilidade por host
        """
        query = """
        SELECT 
            h.host,
            h.name,
            SUM(
                CASE WHEN p.r_eventid IS NOT NULL 
                THEN UNIX_TIMESTAMP(FROM_UNIXTIME(p.r_clock)) - UNIX_TIMESTAMP(FROM_UNIXTIME(p.clock))
                ELSE UNIX_TIMESTAMP() - UNIX_TIMESTAMP(FROM_UNIXTIME(p.clock))
                END
            ) as downtime_seconds,
            (%s * 24 * 3600) as total_seconds,
            (1 - (SUM(
                CASE WHEN p.r_eventid IS NOT NULL 
                THEN UNIX_TIMESTAMP(FROM_UNIXTIME(p.r_clock)) - UNIX_TIMESTAMP(FROM_UNIXTIME(p.clock))
                ELSE UNIX_TIMESTAMP() - UNIX_TIMESTAMP(FROM_UNIXTIME(p.clock))
                END
            ) / (%s * 24 * 3600))) * 100 as availability_percent
        FROM 
            hosts h
        LEFT JOIN 
            problem p ON h.hostid = p.objectid 
                    AND p.source = 0 
                    AND p.object = 0
                    AND p.clock > UNIX_TIMESTAMP() - (%s * 24 * 3600)
        WHERE 
            h.status = 0  -- Host ativo
        GROUP BY 
            h.hostid
        ORDER BY 
            availability_percent ASC
        """
        
        return self.execute_query(query, (period_days, period_days, period_days))
    
    def build_custom_sql_query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Executa uma consulta SQL personalizada
        
        Args:
            sql: Consulta SQL
            params: Parâmetros para a consulta
            
        Returns:
            Resultados da consulta
        """
        # IMPORTANTE: Validação básica para evitar SQL injection
        if any(dangerous_keyword in sql.lower() for dangerous_keyword in [
            "drop", "truncate", "delete", "update", "insert", "alter", "grant"
        ]):
            raise ValueError("Consulta SQL contém comandos não permitidos")
        
        return self.execute_query(sql, params) 