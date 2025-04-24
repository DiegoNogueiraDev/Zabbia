import os
from sqlmodel import SQLModel, Session, create_engine
from typing import Generator

# Configuração do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/zabbia")

# Criar engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Definir como True para ver queries SQL (apenas para desenvolvimento)
    pool_pre_ping=True,
)

def create_db_and_tables():
    """
    Cria as tabelas no banco de dados se elas não existirem.
    """
    SQLModel.metadata.create_all(engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obter uma sessão do banco de dados.
    """
    with Session(engine) as session:
        yield session 