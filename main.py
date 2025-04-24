import logging
import uvicorn
import os
import sys
from pathlib import Path

# Adicionar diretório raiz ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from backend.config import settings

# Configuração de logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    """Função principal para iniciar o servidor Zabbia"""
    logger.info(f"Iniciando servidor Zabbia v{settings.api_version}")
    logger.info(f"Ambiente: {settings.environment}")
    logger.info(f"Configurações: Host={settings.host}, Porta={settings.port}")
    
    # Configurar Uvicorn
    uvicorn.run(
        "backend.api:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        workers=1,
        log_level=settings.log_level.lower()
    )

if __name__ == "__main__":
    main() 