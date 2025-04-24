import logging
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import base64
import io
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union

from zabbia.backend.db_utils import db_client

logger = logging.getLogger(__name__)

class ZabbixChartGenerator:
    """Gerador de gráficos para dados do Zabbix
    
    Esta classe permite gerar gráficos a partir dos dados obtidos do Zabbix,
    utilizando matplotlib para visualização de métricas de monitoramento.
    """
    
    def __init__(self):
        """Inicializa o gerador de gráficos"""
        # Configurações padrão de estilo para os gráficos
        plt.style.use('ggplot')
        
    @staticmethod
    def convert_timestamp_to_datetime(timestamp: int) -> datetime:
        """Converte timestamp Unix para objeto datetime
        
        Args:
            timestamp: Timestamp Unix em segundos
            
        Returns:
            Objeto datetime correspondente
        """
        return datetime.fromtimestamp(timestamp)
    
    @staticmethod
    def format_value_with_units(value: float, units: str) -> str:
        """Formata um valor com suas unidades
        
        Args:
            value: Valor numérico
            units: Unidade de medida
            
        Returns:
            String formatada com valor e unidade
        """
        if not units:
            return str(value)
            
        # Formatação especial para percentuais
        if units == '%':
            return f"{value:.2f}%"
            
        # Formatação para bytes (B, KB, MB, GB, TB)
        if units.lower() in ['b', 'bytes']:
            if value < 1024:
                return f"{value:.2f} B"
            elif value < 1024**2:
                return f"{value/1024:.2f} KB"
            elif value < 1024**3:
                return f"{value/(1024**2):.2f} MB"
            elif value < 1024**4:
                return f"{value/(1024**3):.2f} GB"
            else:
                return f"{value/(1024**4):.2f} TB"
                
        # Caso padrão
        return f"{value:.2f} {units}"
    
    def generate_time_series_chart(
        self,
        item_id: int,
        title: Optional[str] = None,
        time_from: Optional[int] = None,
        time_till: Optional[int] = None,
        width: int = 10,
        height: int = 6,
        color: str = '#1f77b4',
        show_markers: bool = False,
        limit: int = 1000
    ) -> str:
        """Gera um gráfico de série temporal para um item específico
        
        Args:
            item_id: ID do item do Zabbix
            title: Título do gráfico (opcional)
            time_from: Timestamp inicial (opcional)
            time_till: Timestamp final (opcional)
            width: Largura do gráfico em polegadas
            height: Altura do gráfico em polegadas
            color: Cor da linha do gráfico
            show_markers: Se True, exibe marcadores nos pontos de dados
            limit: Limite de pontos de dados
            
        Returns:
            String base64 da imagem do gráfico
        """
        # Busca os dados do item para obter o nome e unidade
        item_info = db_client.execute_query(
            "SELECT name, units FROM items WHERE itemid = %s",
            (item_id,)
        )
        
        if not item_info:
            logger.error(f"Item não encontrado: {item_id}")
            return None
            
        item_name = item_info[0]['name']
        item_units = item_info[0]['units']
        
        # Busca o histórico do item
        history_data = db_client.get_item_history(
            item_id=item_id,
            time_from=time_from,
            time_till=time_till,
            limit=limit
        )
        
        if not history_data:
            logger.error(f"Nenhum dado histórico encontrado para o item: {item_id}")
            return None
            
        # Processa os dados para o gráfico
        timestamps = [self.convert_timestamp_to_datetime(point['clock']) for point in history_data]
        values = [float(point['value']) for point in history_data]
        
        # Inverte as listas para ordem cronológica
        timestamps.reverse()
        values.reverse()
        
        # Configuração do gráfico
        plt.figure(figsize=(width, height))
        
        if show_markers:
            plt.plot(timestamps, values, marker='o', linestyle='-', color=color)
        else:
            plt.plot(timestamps, values, linestyle='-', color=color)
            
        # Formatação do gráfico
        plt.title(title if title else item_name)
        plt.xlabel('Tempo')
        plt.ylabel(item_units if item_units else 'Valor')
        plt.grid(True)
        
        # Formatação do eixo X para datas
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.gcf().autofmt_xdate()
        
        # Converte o gráfico para base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        # Retorna a string base64
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    
    def generate_comparison_chart(
        self,
        item_ids: List[int],
        title: str = "Comparação de Itens",
        time_from: Optional[int] = None,
        time_till: Optional[int] = None,
        width: int = 12,
        height: int = 8,
        limit: int = 500
    ) -> str:
        """Gera um gráfico comparativo de múltiplos itens
        
        Args:
            item_ids: Lista de IDs de itens do Zabbix
            title: Título do gráfico
            time_from: Timestamp inicial (opcional)
            time_till: Timestamp final (opcional)
            width: Largura do gráfico em polegadas
            height: Altura do gráfico em polegadas
            limit: Limite de pontos de dados por item
            
        Returns:
            String base64 da imagem do gráfico
        """
        if not item_ids:
            logger.error("Nenhum item especificado para comparação")
            return None
            
        plt.figure(figsize=(width, height))
        
        # Cores para diferenciação das linhas
        colors = plt.cm.tab10.colors
        
        for idx, item_id in enumerate(item_ids):
            # Busca os dados do item
            item_info = db_client.execute_query(
                "SELECT name, units FROM items WHERE itemid = %s",
                (item_id,)
            )
            
            if not item_info:
                logger.warning(f"Item não encontrado: {item_id}")
                continue
                
            item_name = item_info[0]['name']
            
            # Busca o histórico do item
            history_data = db_client.get_item_history(
                item_id=item_id,
                time_from=time_from,
                time_till=time_till,
                limit=limit
            )
            
            if not history_data:
                logger.warning(f"Nenhum dado histórico encontrado para o item: {item_id}")
                continue
                
            # Processa os dados para o gráfico
            timestamps = [self.convert_timestamp_to_datetime(point['clock']) for point in history_data]
            values = [float(point['value']) for point in history_data]
            
            # Inverte as listas para ordem cronológica
            timestamps.reverse()
            values.reverse()
            
            # Adiciona a linha ao gráfico
            color = colors[idx % len(colors)]
            plt.plot(timestamps, values, linestyle='-', color=color, label=item_name)
            
        # Formatação do gráfico
        plt.title(title)
        plt.xlabel('Tempo')
        plt.ylabel('Valor')
        plt.grid(True)
        plt.legend(loc='best')
        
        # Formatação do eixo X para datas
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.gcf().autofmt_xdate()
        
        # Converte o gráfico para base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        # Retorna a string base64
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    
    def generate_pie_chart(
        self,
        data: List[Dict[str, Any]],
        labels_key: str,
        values_key: str,
        title: str = "Distribuição",
        width: int = 8,
        height: int = 8,
        explode_largest: bool = True
    ) -> str:
        """Gera um gráfico de pizza para visualização de distribuição
        
        Args:
            data: Lista de dicionários com os dados
            labels_key: Chave para os rótulos nos dicionários
            values_key: Chave para os valores nos dicionários
            title: Título do gráfico
            width: Largura do gráfico em polegadas
            height: Altura do gráfico em polegadas
            explode_largest: Se True, destaca a maior fatia
            
        Returns:
            String base64 da imagem do gráfico
        """
        if not data:
            logger.error("Nenhum dado fornecido para o gráfico de pizza")
            return None
            
        # Extrai os rótulos e valores
        labels = [item[labels_key] for item in data]
        values = [float(item[values_key]) for item in data]
        
        # Configura o explode (destacar fatias)
        explode = None
        if explode_largest:
            largest_idx = values.index(max(values))
            explode = [0.1 if i == largest_idx else 0 for i in range(len(values))]
        
        # Configuração do gráfico
        plt.figure(figsize=(width, height))
        plt.pie(
            values, 
            labels=labels, 
            explode=explode,
            autopct='%1.1f%%',
            shadow=True, 
            startangle=90
        )
        plt.axis('equal')  # Iguala a proporção para um círculo perfeito
        plt.title(title)
        
        # Converte o gráfico para base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        # Retorna a string base64
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    
    def generate_bar_chart(
        self,
        data: List[Dict[str, Any]],
        labels_key: str,
        values_key: str,
        title: str = "Comparação",
        xlabel: str = "Categorias",
        ylabel: str = "Valores",
        width: int = 10,
        height: int = 6,
        color: str = '#1f77b4',
        horizontal: bool = False,
        sort_by_value: bool = False
    ) -> str:
        """Gera um gráfico de barras
        
        Args:
            data: Lista de dicionários com os dados
            labels_key: Chave para os rótulos nos dicionários
            values_key: Chave para os valores nos dicionários
            title: Título do gráfico
            xlabel: Rótulo do eixo X
            ylabel: Rótulo do eixo Y
            width: Largura do gráfico em polegadas
            height: Altura do gráfico em polegadas
            color: Cor das barras
            horizontal: Se True, gera um gráfico de barras horizontais
            sort_by_value: Se True, ordena as barras pelo valor
            
        Returns:
            String base64 da imagem do gráfico
        """
        if not data:
            logger.error("Nenhum dado fornecido para o gráfico de barras")
            return None
            
        # Extrai os rótulos e valores
        chart_data = [(item[labels_key], float(item[values_key])) for item in data]
        
        # Ordena os dados se necessário
        if sort_by_value:
            chart_data.sort(key=lambda x: x[1], reverse=True)
            
        labels = [item[0] for item in chart_data]
        values = [item[1] for item in chart_data]
        
        # Configuração do gráfico
        plt.figure(figsize=(width, height))
        
        if horizontal:
            plt.barh(labels, values, color=color)
            plt.xlabel(ylabel)  # Invertidos para barras horizontais
            plt.ylabel(xlabel)
        else:
            plt.bar(labels, values, color=color)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.xticks(rotation=45, ha='right')
            
        plt.title(title)
        plt.tight_layout()
        
        # Converte o gráfico para base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        # Retorna a string base64
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    
    def generate_resource_usage_chart(
        self,
        host_id: Optional[int] = None,
        host_name: Optional[str] = None,
        resource_type: str = 'cpu',  # 'cpu', 'memory', 'disk'
        time_period: str = '24h',    # '1h', '6h', '24h', '7d', '30d'
        width: int = 10,
        height: int = 6
    ) -> str:
        """Gera um gráfico de uso de recursos para um host específico
        
        Args:
            host_id: ID do host (opcional se host_name for fornecido)
            host_name: Nome do host (opcional se host_id for fornecido)
            resource_type: Tipo de recurso ('cpu', 'memory', 'disk')
            time_period: Período de tempo ('1h', '6h', '24h', '7d', '30d')
            width: Largura do gráfico em polegadas
            height: Altura do gráfico em polegadas
            
        Returns:
            String base64 da imagem do gráfico
        """
        if not host_id and not host_name:
            logger.error("É necessário fornecer host_id ou host_name")
            return None
            
        # Converte o período de tempo para segundos a partir de agora
        time_mapping = {
            '1h': 3600,
            '6h': 21600,
            '24h': 86400,
            '7d': 604800,
            '30d': 2592000
        }
        
        if time_period not in time_mapping:
            logger.error(f"Período de tempo inválido: {time_period}")
            return None
            
        time_from = int(datetime.now().timestamp()) - time_mapping[time_period]
        
        # Obtém o host_id se apenas o nome foi fornecido
        if not host_id and host_name:
            host_info = db_client.execute_query(
                "SELECT hostid FROM hosts WHERE name LIKE %s AND status = 0",
                (f"%{host_name}%",)
            )
            
            if not host_info:
                logger.error(f"Host não encontrado: {host_name}")
                return None
                
            host_id = host_info[0]['hostid']
        
        # Determina o padrão de chave e título com base no tipo de recurso
        key_pattern = None
        title = None
        
        if resource_type == 'cpu':
            key_pattern = 'system.cpu.util'
            title = f"Uso de CPU - {time_period}"
        elif resource_type == 'memory':
            key_pattern = 'vm.memory.util'
            title = f"Uso de Memória - {time_period}"
        elif resource_type == 'disk':
            key_pattern = 'vfs.fs.size[/,pused]'  # Ajustar conforme necessário
            title = f"Uso de Disco (/) - {time_period}"
        else:
            logger.error(f"Tipo de recurso inválido: {resource_type}")
            return None
        
        # Busca o item correspondente
        items = db_client.execute_query(
            "SELECT itemid, name FROM items WHERE hostid = %s AND key_ LIKE %s AND status = 0",
            (host_id, f"%{key_pattern}%")
        )
        
        if not items:
            logger.error(f"Item não encontrado para o host {host_id} com padrão {key_pattern}")
            return None
            
        # Usa o primeiro item encontrado
        item_id = items[0]['itemid']
        item_name = items[0]['name']
        
        # Gera o gráfico de série temporal para o item
        return self.generate_time_series_chart(
            item_id=item_id,
            title=f"{title} - {item_name}",
            time_from=time_from,
            width=width,
            height=height
        )

# Instância global do gerador de gráficos
chart_generator = ZabbixChartGenerator() 