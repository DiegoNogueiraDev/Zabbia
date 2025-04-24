from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from datetime import datetime
import jwt
from typing import Optional

from app.services.licensing import verify_license, generate_license

router = APIRouter()

class LicenseInfo(BaseModel):
    key: str
    customer: str
    expires: datetime
    seats: int
    valid: bool
    days_remaining: Optional[int] = None

class LicenseRequest(BaseModel):
    license_key: str

class GenerateLicenseRequest(BaseModel):
    customer: str
    seats: int
    days: int
    secret_key: str  # Chave secreta para autorizar a geração

@router.post("/validate", response_model=LicenseInfo)
async def validate_license_key(
    request: LicenseRequest = Body(...)
):
    """
    Valida uma chave de licença e retorna informações sobre ela.
    """
    try:
        is_valid, error_or_info = verify_license(request.license_key)
        
        if not is_valid:
            return LicenseInfo(
                key=request.license_key,
                customer="",
                expires=datetime.now(),
                seats=0,
                valid=False
            )
        
        # Calcular dias restantes
        days_remaining = (error_or_info["expires"] - datetime.now()).days
        
        return LicenseInfo(
            key=request.license_key,
            customer=error_or_info["customer"],
            expires=error_or_info["expires"],
            seats=error_or_info["seats"],
            valid=True,
            days_remaining=days_remaining
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao validar licença: {str(e)}")

@router.post("/generate")
async def create_license(
    request: GenerateLicenseRequest
):
    """
    Endpoint protegido para gerar uma nova licença.
    Requer chave secreta para autorização.
    """
    # Verificar chave secreta (normalmente seria implementado com autenticação adequada)
    if request.secret_key != "ZABBIA_ADMIN_SECRET":  # Em produção, usar variável de ambiente
        raise HTTPException(status_code=403, detail="Não autorizado a gerar licenças")
    
    try:
        # Gerar licença
        license_key = generate_license(
            customer=request.customer,
            seats=request.seats,
            days=request.days
        )
        
        return {
            "license_key": license_key,
            "customer": request.customer,
            "seats": request.seats,
            "expires_in_days": request.days
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar licença: {str(e)}") 