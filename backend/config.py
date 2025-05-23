import os
import logging
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pydantic_settings import BaseSettings

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

@dataclass
class ZabbiaConfig:
    """Classe de configuração para o Zabbia"""
    
    # Configurações do banco de dados Zabbix
    zabbix_db_host: str = "localhost"
    zabbix_db_port: int = 3306
    zabbix_db_name: str = "zabbix"
    zabbix_db_user: str = "zabbix"
    zabbix_db_password: str = ""
    
    # Configurações da API Zabbix
    zabbix_api_url: str = "http://localhost/zabbix/api_jsonrpc.php"
    zabbix_username: str = "Admin"
    zabbix_password: str = "zabbix"
    api_version: str = "6.0"
    
    # Configurações do Zabbia
    log_level: str = "INFO"
    cache_timeout: int = 300  # 5 minutos
    result_limit: int = 1000
    timezone: str = "America/Sao_Paulo"
    
    def __post_init__(self):
        """Ajusta o nível de log com base na configuração"""
        logging.getLogger().setLevel(getattr(logging, self.log_level))

    @classmethod
    def from_file(cls, config_path: str) -> 'ZabbiaConfig':
        """Carrega configurações de um arquivo JSON
        
        Args:
            config_path: Caminho para o arquivo de configuração
            
        Returns:
            Instância de ZabbiaConfig com os valores do arquivo
        """
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    
                    # Verificar se o arquivo usa a estrutura antiga com 'zabbix'
                    if 'zabbix' in config_data:
                        # Converter formato antigo para o novo
                        zabbix_data = config_data['zabbix']
                        zabbix_db = zabbix_data.get('db', {})
                        
                        new_config = {
                            'zabbix_api_url': zabbix_data.get('api_url'),
                            'zabbix_username': zabbix_data.get('username'),
                            'zabbix_password': zabbix_data.get('password'),
                            'zabbix_db_host': zabbix_db.get('host'),
                            'zabbix_db_port': zabbix_db.get('port'),
                            'zabbix_db_name': zabbix_db.get('name'),
                            'zabbix_db_user': zabbix_db.get('user'),
                            'zabbix_db_password': zabbix_db.get('password'),
                        }
                        
                        # Adicionar outras configurações
                        if 'logging' in config_data:
                            new_config['log_level'] = config_data['logging'].get('level')
                        
                        if 'server' in config_data:
                            new_config['server_host'] = config_data['server'].get('host')
                            new_config['server_port'] = config_data['server'].get('port')
                            new_config['server_workers'] = config_data['server'].get('workers')
                        
                        if 'cache' in config_data:
                            new_config['cache_url'] = config_data['cache'].get('url')
                            new_config['cache_timeout'] = config_data['cache'].get('timeout_seconds')
                        
                        return cls(**new_config)
                        
                    # Se usar o formato novo, usa diretamente
                    return cls(**config_data)
            else:
                logger.warning(f"Arquivo de configuração não encontrado: {config_path}")
                return cls()
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo de configuração: {e}")
            return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a configuração para dicionário
        
        Returns:
            Dicionário com os valores de configuração
        """
        return {k: v for k, v in self.__dict__.items()}
    
    def save_to_file(self, config_path: str) -> bool:
        """Salva as configurações em um arquivo JSON
        
        Args:
            config_path: Caminho para o arquivo de configuração
            
        Returns:
            True se salvo com sucesso, False caso contrário
        """
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=4)
            logger.info(f"Configurações salvas em: {config_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
            return False


# Carrega configurações do arquivo ou usa os valores padrão
CONFIG_PATH = os.environ.get("ZABBIA_CONFIG", "config/zabbia.json")
settings = ZabbiaConfig.from_file(CONFIG_PATH)

class Settings(BaseSettings):
    """Configurações globais da aplicação"""
    
    # Versão da API
    api_version: str = "0.1.0"
    
    # Configurações de ambiente
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "development")
    is_development: bool = os.getenv("ENVIRONMENT", "development") == "development"
    
    # Configurações do servidor
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    server_host: str = os.getenv("SERVER_HOST", "0.0.0.0")
    server_port: int = int(os.getenv("SERVER_PORT", "8000"))
    server_workers: int = int(os.getenv("SERVER_WORKERS", "1"))
    
    # Configurações CORS
    cors_origins: list = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
    
    # Configurações da API Zabbix
    zabbix_url: str = os.getenv("ZABBIX_URL", "http://localhost/zabbix/api_jsonrpc.php")
    zabbix_username: str = os.getenv("ZABBIX_USERNAME", "Admin")
    zabbix_password: str = os.getenv("ZABBIX_PASSWORD", "zabbix")
    
    # Configurações do banco de dados
    database_url: Optional[str] = os.getenv("DATABASE_URL", None)
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_user: str = os.getenv("DB_USER", "zabbix")
    db_password: str = os.getenv("DB_PASSWORD", "zabbix")
    db_name: str = os.getenv("DB_NAME", "zabbix")
    
    # Configurações de cache
    use_cache: bool = os.getenv("USE_CACHE", "True").lower() == "true"
    cache_ttl: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutos
    
    # Configurações de log
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Configurações de autenticação
    secret_key: str = os.getenv("SECRET_KEY", "zabbia-dev-secret-key")
    token_expire_minutes: int = int(os.getenv("TOKEN_EXPIRE_MINUTES", "30"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings() 