import jwt
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple, Union, Any, Optional
from fastapi import Depends
from sqlmodel import Session, select

from app.services.database import get_db
from app.domain.models import License

# Chave para assinar os tokens JWT (em produção, usar variável de ambiente)
JWT_SECRET = os.getenv("JWT_SECRET", "zabbia_license_secret_key")

def generate_license(customer: str, seats: int, days: int) -> str:
    """
    Gera uma chave de licença JWT.
    """
    # Calcular data de expiração
    now = datetime.utcnow()
    expires = now + timedelta(days=days)
    
    # Criar payload
    payload = {
        "iss": "zabbia_licensing",
        "iat": now.timestamp(),
        "exp": expires.timestamp(),
        "sub": customer,
        "seats": seats,
        "customer": customer
    }
    
    # Assinar JWT
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    # Salvar licença no banco
    # Isso seria feito no contexto de uma sessão de banco de dados
    # Em um caso real, você passaria a sessão como parâmetro
    
    return token

def verify_license(license_key: str) -> Tuple[bool, Union[str, Dict[str, Any]]]:
    """
    Verifica se uma licença é válida.
    Retorna uma tupla (is_valid, error_or_info).
    """
    try:
        # Verificar JWT
        payload = jwt.decode(license_key, JWT_SECRET, algorithms=["HS256"])
        
        # Verificar se expirou
        if "exp" in payload and payload["exp"] < datetime.utcnow().timestamp():
            return False, "Licença expirada"
        
        # Retornar informações da licença
        license_info = {
            "customer": payload.get("customer", ""),
            "seats": payload.get("seats", 0),
            "expires": datetime.fromtimestamp(payload.get("exp", 0)),
            "issued": datetime.fromtimestamp(payload.get("iat", 0))
        }
        
        return True, license_info
    
    except jwt.ExpiredSignatureError:
        return False, "Licença expirada"
    
    except jwt.InvalidTokenError:
        return False, "Licença inválida"
    
    except Exception as e:
        return False, f"Erro ao verificar licença: {str(e)}"

def check_license_db(
    license_key: str, 
    session: Session = Depends(get_db)
) -> Tuple[bool, Union[str, Dict[str, Any]]]:
    """
    Verifica licença no banco de dados (para revogação).
    """
    # Primeiro, verificar validade criptográfica
    is_valid, info = verify_license(license_key)
    
    if not is_valid:
        return is_valid, info
    
    # Se válida, verificar se foi revogada no banco
    if isinstance(info, dict) and "customer" in info:
        license_db = session.exec(
            select(License).where(License.key == license_key)
        ).first()
        
        # Se licença existe no banco e está revogada
        if license_db and license_db.revoked:
            return False, f"Licença revogada: {license_db.revocation_reason}"
    
    return is_valid, info

def revoke_license(
    license_key: str, 
    reason: str, 
    session: Session = Depends(get_db)
) -> bool:
    """
    Revoga uma licença.
    """
    # Verificar se a licença é válida
    is_valid, info = verify_license(license_key)
    
    if not is_valid:
        return False
    
    # Verificar se a licença já existe no banco
    license_db = session.exec(
        select(License).where(License.key == license_key)
    ).first()
    
    if license_db:
        # Atualizar licença existente
        license_db.revoked = True
        license_db.revocation_reason = reason
        license_db.updated_at = datetime.utcnow()
    else:
        # Criar nova entrada para a licença revogada
        if isinstance(info, dict):
            license_db = License(
                key=license_key,
                customer=info.get("customer", ""),
                expires=info.get("expires", datetime.utcnow()),
                seats=info.get("seats", 0),
                revoked=True,
                revocation_reason=reason
            )
            session.add(license_db)
    
    session.commit()
    return True 