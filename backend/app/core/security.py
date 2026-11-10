"""Utilitários e dependências base de segurança da aplicação."""

from fastapi.security import HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False)

