import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ZabbixAnalyzer:
    """
    Classe utilitária para análise de dados do Zabbix.
    Fornece métodos para processamento e análise de dados obtidos da API do Zabbix.
    """
    
    @staticmethod
    def process_history_data(history_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Converte dados históricos do Zabbix em um DataFrame do pandas.
        
        Args:
            history_data: Lista de dicionários contendo dados históricos do Zabbix
            
        Returns:
            DataFrame com os dados processados
        """
        if not history_data:
            return pd.DataFrame()
            
        try:
            df = pd.DataFrame(history_data)
            
            # Converter timestamp para datetime
            if 'clock' in df.columns:
                df['timestamp'] = pd.to_datetime(df['clock'].astype(int), unit='s')
                
            # Converter valor para numérico se possível
            if 'value' in df.columns:
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                
            return df
        except Exception as e:
            logger.error(f"Erro ao processar dados históricos: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def detect_anomalies(df: pd.DataFrame, value_col: str = 'value', window: int = 10, threshold: float = 2.0) -> pd.DataFrame:
        """
        Detecta anomalias nos dados usando o método do desvio padrão.
        
        Args:
            df: DataFrame com os dados
            value_col: Nome da coluna com os valores
            window: Tamanho da janela para cálculo da média móvel
            threshold: Limite de desvios padrão para considerar um ponto como anomalia
            
        Returns:
            DataFrame com uma coluna adicional 'is_anomaly' (True/False)
        """
        if df.empty or value_col not in df.columns:
            return df
            
        result_df = df.copy()
        
        try:
            # Calcular média móvel e desvio padrão
            rolling_mean = df[value_col].rolling(window=window, center=True).mean()
            rolling_std = df[value_col].rolling(window=window, center=True).std()
            
            # Identificar anomalias
            result_df['is_anomaly'] = (
                (df[value_col] > (rolling_mean + threshold * rolling_std)) | 
                (df[value_col] < (rolling_mean - threshold * rolling_std))
            )
            
            # Preencher NaN com False
            result_df['is_anomaly'] = result_df['is_anomaly'].fillna(False)
            
            return result_df
        except Exception as e:
            logger.error(f"Erro ao detectar anomalias: {e}")
            return df
    
    @staticmethod
    def generate_trend_prediction(df: pd.DataFrame, value_col: str = 'value', 
                                periods_ahead: int = 5) -> Tuple[List[float], List[float]]:
        """
        Gera uma previsão simples de tendência usando médias móveis.
        
        Args:
            df: DataFrame com os dados históricos
            value_col: Nome da coluna com os valores
            periods_ahead: Número de períodos à frente para prever
            
        Returns:
            Tupla contendo (valores_previstos, limites_confiança)
        """
        if df.empty or value_col not in df.columns:
            return ([], [])
            
        try:
            # Usar média móvel exponencial para previsão simples
            values = df[value_col].values
            
            # Calcular média móvel exponencial
            alpha = 0.3  # Fator de suavização
            ema = [values[0]]
            
            for i in range(1, len(values)):
                ema.append(alpha * values[i] + (1 - alpha) * ema[i-1])
            
            # Prever próximos valores
            last_ema = ema[-1]
            forecast = [last_ema] * periods_ahead
            
            # Calcular limites de confiança simples (desvio padrão dos últimos n pontos)
            std = np.std(values[-10:]) if len(values) >= 10 else np.std(values)
            confidence = [1.96 * std] * periods_ahead  # 95% de confiança
            
            return (forecast, confidence)
        except Exception as e:
            logger.error(f"Erro ao gerar previsão de tendência: {e}")
            return ([], [])
    
    @staticmethod
    def generate_chart(df: pd.DataFrame, value_col: str = 'value', 
                       time_col: str = 'timestamp', title: str = 'Dados do Zabbix',
                       include_prediction: bool = False, periods_ahead: int = 5) -> str:
        """
        Gera um gráfico a partir dos dados e o retorna como uma string base64.
        
        Args:
            df: DataFrame com os dados
            value_col: Nome da coluna com os valores
            time_col: Nome da coluna com o timestamp
            title: Título do gráfico
            include_prediction: Se deve incluir previsão de tendência
            periods_ahead: Número de períodos à frente para prever
            
        Returns:
            String base64 do gráfico em formato PNG
        """
        if df.empty or value_col not in df.columns or time_col not in df.columns:
            return ""
            
        try:
            plt.figure(figsize=(10, 6))
            
            # Plotar dados reais
            plt.plot(df[time_col], df[value_col], 'b-', label='Dados Reais')
            
            # Destacar anomalias, se existirem
            if 'is_anomaly' in df.columns:
                anomalies = df[df['is_anomaly'] == True]
                if not anomalies.empty:
                    plt.scatter(anomalies[time_col], anomalies[value_col], 
                                color='red', label='Anomalias', zorder=5)
            
            # Adicionar previsão, se solicitado
            if include_prediction and not df.empty:
                prediction, confidence = ZabbixAnalyzer.generate_trend_prediction(
                    df, value_col, periods_ahead
                )
                
                if prediction and len(df) > 0:
                    # Criar datas futuras
                    last_date = df[time_col].iloc[-1]
                    if isinstance(last_date, pd.Timestamp):
                        future_dates = [last_date + timedelta(hours=i+1) for i in range(periods_ahead)]
                    else:
                        future_dates = [datetime.now() + timedelta(hours=i+1) for i in range(periods_ahead)]
                    
                    # Plotar previsão
                    plt.plot(future_dates, prediction, 'g--', label='Previsão')
                    
                    # Plotar intervalo de confiança
                    upper = [p + c for p, c in zip(prediction, confidence)]
                    lower = [p - c for p, c in zip(prediction, confidence)]
                    plt.fill_between(future_dates, lower, upper, color='g', alpha=0.2, 
                                    label='Intervalo de Confiança (95%)')
            
            # Formatar gráfico
            plt.title(title)
            plt.xlabel('Tempo')
            plt.ylabel('Valor')
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.legend()
            plt.tight_layout()
            
            # Converter para base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close()
            
            return image_base64
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico: {e}")
            return ""
    
    @staticmethod
    def summarize_problems(problems: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sumariza os problemas por serviço e severidade.
        
        Args:
            problems: Lista de problemas do Zabbix
            
        Returns:
            Dicionário com resumo dos problemas
        """
        if not problems:
            return {
                "total": 0,
                "by_severity": {},
                "by_host": {},
                "recent": []
            }
            
        try:
            # Mapear severidade para texto
            severity_map = {
                '0': 'Não classificado',
                '1': 'Informação',
                '2': 'Aviso',
                '3': 'Médio',
                '4': 'Alto',
                '5': 'Crítico'
            }
            
            # Inicializar contadores
            by_severity = {severity: 0 for severity in severity_map.values()}
            by_host = {}
            
            # Processar cada problema
            for problem in problems:
                # Contar por severidade
                severity = severity_map.get(str(problem.get('severity', '0')), 'Desconhecido')
                by_severity[severity] = by_severity.get(severity, 0) + 1
                
                # Contar por host
                host = problem.get('host', 'Desconhecido')
                by_host[host] = by_host.get(host, 0) + 1
            
            # Ordenar problemas recentes por timestamp (mais recentes primeiro)
            sorted_problems = sorted(
                problems, 
                key=lambda x: int(x.get('clock', 0)), 
                reverse=True
            )
            
            # Pegar os 5 problemas mais recentes
            recent = sorted_problems[:5]
            
            # Formatar os problemas recentes
            formatted_recent = []
            for p in recent:
                formatted_recent.append({
                    "nome": p.get('name', 'Sem descrição'),
                    "host": p.get('host', 'Desconhecido'),
                    "severidade": severity_map.get(str(p.get('severity', '0')), 'Desconhecido'),
                    "horario": datetime.fromtimestamp(int(p.get('clock', 0))).strftime('%Y-%m-%d %H:%M:%S'),
                    "reconhecido": p.get('acknowledged', '0') == '1'
                })
            
            return {
                "total": len(problems),
                "by_severity": by_severity,
                "by_host": by_host,
                "recent": formatted_recent
            }
        except Exception as e:
            logger.error(f"Erro ao sumarizar problemas: {e}")
            return {
                "total": len(problems),
                "by_severity": {},
                "by_host": {},
                "recent": []
            } 