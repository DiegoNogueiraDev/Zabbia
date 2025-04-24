from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Optional

from app.api.routers import metrics, chat, settings, license
from app.services.licensing import verify_license

def create_app() -> FastAPI:
    app = FastAPI(
        title="Zabbia API",
        description="API para o copiloto de infraestrutura Zabbia com integração ao Zabbix",
        version="1.0.0",
    )
    
    # Configuração CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Em produção, restringir para domínios específicos
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Middleware para verificação de licença
    @app.middleware("http")
    async def license_middleware(request, call_next):
        # Ignorar verificação de licença para rotas públicas
        if request.url.path in ["/docs", "/redoc", "/openapi.json", "/api/license/validate"]:
            return await call_next(request)
        
        # Verificar licença no cabeçalho
        license_key = request.headers.get("X-License-Key")
        if not license_key:
            return HTTPException(status_code=401, detail="Licença não fornecida")
        
        # Validar licença
        is_valid, error = verify_license(license_key)
        if not is_valid:
            return HTTPException(status_code=401, detail=error)
        
        return await call_next(request)
    
    # Incluir routers
    app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
    app.include_router(license.router, prefix="/api/license", tags=["license"])
    
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 