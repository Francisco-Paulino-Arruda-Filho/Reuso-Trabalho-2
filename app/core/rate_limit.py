
from fastapi import HTTPException

from ..infra.supabase_client import supabase
from datetime import datetime, timedelta

WINDOW_SECONDS = 5         # janela de 5 segundos
MAX_REQUESTS = 10          # no máximo 10 req por janela

async def check_rate_limit(cnpj: str):
    now = datetime.now(datetime.timezone.utc)
    result = (
        supabase
        .table("rate_limit")
        .select("*")
        .eq("cnpj", cnpj)
        .execute()
    )

    if len(result.data) == 0:
        supabase.table("rate_limit").insert({
            "cnpj": cnpj,
            "window_start": now.isoformat(),
            "count": 1
        }).execute()
        return

    row = result.data[0]
    window_start = datetime.fromisoformat(row["window_start"])
    count = row["count"]

    if now - window_start > timedelta(seconds=WINDOW_SECONDS):
        supabase.table("rate_limit") \
            .update({"window_start": now.isoformat(), "count": 1}) \
            .eq("cnpj", cnpj).execute()
        return

    if count >= MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit excedido para o CNPJ {cnpj}"
        )

    supabase.table("rate_limit") \
        .update({"count": count + 1}) \
        .eq("cnpj", cnpj).execute()
