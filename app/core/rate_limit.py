from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.responses import Response
from datetime import datetime, timezone, timedelta

WINDOW_SECONDS = 5         # janela de 5 segundos
MAX_REQUESTS = 10          # no máximo 10 req por janela

# Armazenamento em memória para rate limit por IP
# Substituir por redis
_rate_limit_store: dict[str, dict] = {}


def get_client_ip(request: Request) -> str:
    """Extrai o IP do cliente da requisição."""
    forwarded = request.headers.get("X-Forwarded-For")

    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def check_rate_limit(request: Request) -> Response | None:
    """Verifica rate limit baseado no IP do cliente."""
    client_ip = get_client_ip(request)
    now = datetime.now(timezone.utc)

    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = {
            "window_start": now,
            "count": 1
        }
        return None

    entry = _rate_limit_store[client_ip]
    window_start = entry["window_start"]
    count = entry["count"]

    if now - window_start > timedelta(seconds=WINDOW_SECONDS):
        _rate_limit_store[client_ip] = {
            "window_start": now,
            "count": 1
        }
        return None

    if count >= MAX_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={"detail": f"Rate limit excedido para o IP {client_ip}"}
        )

    _rate_limit_store[client_ip]["count"] = count + 1
    return None
