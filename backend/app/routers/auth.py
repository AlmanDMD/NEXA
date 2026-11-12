"""Router de Autenticação, Registro, Renovação e Encerramento de Sessão (EPIC-01 / BE-005 / BE-006 / BE-007 / BE-010)."""

from fastapi import APIRouter, Request, Response, status

from app.core.config import SettingsDep
from app.core.security import CurrentUserDep
from app.schemas.auth import (
    LoginRequestSchema,
    LogoutResponseSchema,
    RefreshTokenResponseSchema,
    TokenResponseSchema,
    UserMeResponse,
)
from app.schemas.user import UserCreateSchema, UserResponseSchema
from app.services.auth_service import AuthServiceDep

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


def _extract_client_ip(request: Request) -> str | None:
    """Extrai o endereço IP do cliente considerando X-Forwarded-For ou conexão direta."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        first_ip = forwarded_for.split(",")[0].strip()
        if first_ip:
            return first_ip[:45]
    if request.client and request.client.host:
        return request.client.host[:45]
    return None


@router.post(
    "/register",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo usuário",
)
async def register(
    payload: UserCreateSchema,
    auth_service: AuthServiceDep,
) -> UserResponseSchema:
    """Registra um novo usuário com hash Bcrypt seguro e perfil opcional."""
    return auth_service.register_user(payload)


@router.post(
    "/login",
    response_model=TokenResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Autenticar usuário e emitir JWT + Refresh Cookie",
)
async def login(
    credentials: LoginRequestSchema,
    request: Request,
    response: Response,
    auth_service: AuthServiceDep,
    settings: SettingsDep,
) -> TokenResponseSchema:
    """Valida credenciais (e-mail e senha), emite Access Token JWT (15m) e Refresh Token em Cookie HttpOnly (7d)."""
    user_agent = request.headers.get("user-agent")
    ip_address = _extract_client_ip(request)

    token_response, refresh_token = auth_service.authenticate_user(
        credentials,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=settings.REFRESH_COOKIE_PATH,
    )

    return token_response


@router.post(
    "/refresh",
    response_model=RefreshTokenResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Renovar sessão e rotacionar Refresh Token",
)
async def refresh(
    request: Request,
    response: Response,
    auth_service: AuthServiceDep,
    settings: SettingsDep,
) -> RefreshTokenResponseSchema:
    """Lê o cookie HttpOnly refresh_token, valida a sessão no banco, realiza Token Rotation e emite novo Access Token."""
    raw_refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    user_agent = request.headers.get("user-agent")
    ip_address = _extract_client_ip(request)

    refresh_response, new_refresh_token = auth_service.refresh_session(
        raw_refresh_token,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=settings.REFRESH_COOKIE_PATH,
    )

    return refresh_response


@router.post(
    "/logout",
    response_model=LogoutResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Encerrar sessão do usuário e invalidar refresh token",
)
async def logout(
    request: Request,
    response: Response,
    auth_service: AuthServiceDep,
    settings: SettingsDep,
) -> LogoutResponseSchema:
    """Invalida a sessão no banco de dados (is_revoked=True) e limpa o cookie HttpOnly refresh_token."""
    raw_refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not raw_refresh_token:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                body = await request.json()
                if isinstance(body, dict):
                    raw_refresh_token = body.get("refresh_token")
            except Exception:
                pass

    ip_address = _extract_client_ip(request)
    logout_response = auth_service.logout(
        raw_refresh_token,
        ip_address=ip_address,
    )

    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path=settings.REFRESH_COOKIE_PATH,
        httponly=True,
        secure=True,
        samesite="lax",
    )

    return logout_response


@router.get(
    "/me",
    response_model=UserMeResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar dados do usuário autenticado atual",
)
async def get_me(
    response: Response,
    current_user: CurrentUserDep,
) -> UserMeResponse:
    """Retorna os dados cadastrais e perfil completo do usuário autenticado sem expor senha ou tokens."""
    response.headers["Cache-Control"] = "no-store"
    return UserMeResponse.model_validate(current_user)


__all__ = ["router"]

