from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import Optional, Any, Dict, Protocol, runtime_checkable

from fastapi import Depends
from fastapi.encoders import jsonable_encoder

from app.infra.supabase_client import get_supabase_client
from app.models.nfe import NFe
from app.common.patterns.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    retry_with_circuit_breaker,
    ExponentialBackoff,
)

circuit_breaker_config = CircuitBreakerConfig(
    failure_threshold=5,
    reset_timeout=timedelta(seconds=60),
    retry_timeout=timedelta(seconds=10),
)

nfe_circuit_breaker = CircuitBreaker(circuit_breaker_config)


@runtime_checkable
class NFeServiceProtocol(Protocol):
    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]: ...

    async def update(self, record_id: str,
               update_payload: Dict[str, Any]) -> Dict[str, Any]: ...

    async def update_status(self, record_id: str, status: str,
                      payload_retorno: Optional[Any] = None, expected_current_status: Optional[str] = None) -> Optional[Dict[str, Any]]: ...

    async def mark_error(self, record_id: str, error: Any) -> Dict[str, Any]: ...

    async def get_all(self) -> Any: ...

class NFeService:
    """Service encapsulating common operations on the `nfe` Supabase table.
    """

    def __init__(self, client=Depends(get_supabase_client)):
        self.client = client or get_supabase_client()
        self.circuit_breaker = nfe_circuit_breaker

    async def insert(self, record: Dict[str, Any]) -> Dict[str, Any]:
        insert_op = self.client.table("nfe").insert(record)

        try:
            backoff = ExponentialBackoff(initial_delay=1.0, max_delay=10.0, max_attemps=4, jitter=True)
            resp = await retry_with_circuit_breaker(
                lambda: insert_op.execute(),
                self.circuit_breaker,
                backoff,
            )

            if getattr(resp, "error", None):
                raise Exception(resp.error)
            if not resp.data:
                raise Exception("Falha ao inserir NF-e no Supabase")
            return resp.data[0]
        except Exception as exc:
            raise Exception(f"Falha ao inserir NF-e no Supabase: {exc}")

    def _generate_ref(self, agora: datetime) -> str:
        return f"{agora.strftime('%y%m%d%H%M%S')}{uuid4().hex[:6]}"
    
    def get_all(self) -> Any:
        return self.client.table("nfe").select("*").execute()

    async def create_from_model(self, nfe: NFe, xml_str: Optional[str] = None) -> Dict[str, Any]:
        agora = datetime.now(timezone.utc)

        payload = {
            "id": str(uuid4()),
            "ref": None,
            "status": "CRIADA",
            "chave_nfe": None,
            "numero": None,
            "serie": None,
            "xml_url": None,
            "danfe_url": None,
            "payload_envio": jsonable_encoder(nfe),
            "payload_retorno": None,
            "ambiente": "producao",
            "data_emissao": (
                nfe.data_emissao.isoformat() if getattr(nfe, "data_emissao", None) else None
            ),
            "autorizado_em": None,
            "criado_em": agora.isoformat(),
            "atualizado_em": agora.isoformat(),
        }

        try:
            payload["ref"] = self._generate_ref(agora)
            return await self.insert(payload)
        except Exception as exc:
            raise Exception(f"Falha ao gerar ou salvar NF-e: {exc}")

    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        try:
            backoff = ExponentialBackoff(initial_delay=0.5, max_delay=5.0, max_attemps=3, jitter=True)

            def op():
                return self.client.table("nfe").select("*").eq("id", record_id).execute()

            resp = await retry_with_circuit_breaker(
                op,
                self.circuit_breaker,
                backoff,
            )

            if not resp.data:
                return None
            return resp.data[0]
        except Exception as exc:
            raise Exception(f"Falha ao buscar NF-e por id no Supabase: {exc}")

    async def update(self, record_id: str, update_payload: Dict[str, Any]) -> Dict[str, Any]:
        update_op = self.client.table("nfe").update(
            update_payload).eq("id", record_id)

        try:
            backoff = ExponentialBackoff(initial_delay=0.5, max_delay=5.0, max_attemps=3, jitter=True)
            resp = await retry_with_circuit_breaker(
                lambda: update_op.execute(),
                self.circuit_breaker,
                backoff,
            )

            if getattr(resp, "error", None):
                raise Exception(resp.error)

            return resp.data[0]
        except Exception as exc:
            raise Exception(f"Falha ao atualizar NF-e no Supabase: {exc}")

    async def update_status(self, record_id: str, status: str, payload_retorno: Optional[Any] = None, expected_current_status: Optional[str] = None) -> Optional[Dict[str, Any]]:
        payload = {"status": status, "atualizado_em": datetime.now(
            timezone.utc).isoformat()}
        if payload_retorno is not None:
            payload["payload_retorno"] = payload_retorno

        query = self.client.table("nfe").update(payload).eq("id", record_id)

        if expected_current_status is not None:
            query = query.eq("status", expected_current_status)

        try:
            backoff = ExponentialBackoff(initial_delay=0.5, max_delay=5.0, max_attemps=3, jitter=True)
            resp = await retry_with_circuit_breaker(
                lambda: query.execute(),
                self.circuit_breaker,
                backoff,
            )
            if getattr(resp, "error", None):
                raise Exception(resp.error)
            return resp.data[0]
        except Exception as exc:
            raise Exception(f"Falha ao atualizar status da NF-e no Supabase: {exc}")

    async def mark_error(self, record_id: str, error: Any) -> Dict[str, Any]:
        return await self.update_status(record_id, "ERRO", {"error": str(error)})


__all__ = ["NFeService", "NFeServiceProtocol"]
