from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional, Any, Dict, Protocol, runtime_checkable

from fastapi.encoders import jsonable_encoder

from app.infra.supabase_client import supabase
from app.models.nfe import NFe


@runtime_checkable
class NFeServiceProtocol(Protocol):
    def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]: ...

    def update(self, record_id: str, update_payload: Dict[str, Any]) -> Dict[str, Any]: ...

    def update_status(self, record_id: str, status: str, payload_retorno: Optional[Any] = None, expected_current_status: Optional[str] = None) -> Optional[Dict[str, Any]]: ...

    def mark_error(self, record_id: str, error: Any) -> Dict[str, Any]: ...

class NFeService:
    """Service encapsulating common operations on the `nfe` Supabase table.
    """

    def __init__(self, client=None):
        self.client = client or supabase

    def insert(self, record: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.client.table("nfe").insert(record).execute()
        if not resp.data:
            raise Exception("Falha ao inserir NF-e no Supabase")
        return resp.data[0]

    def create_from_model(self, nfe: NFe, xml_str: Optional[str] = None) -> Dict[str, Any]:
        agora = datetime.now(timezone.utc)

        payload = {
            "id": str(uuid4()),
            "ref": agora.strftime("%y%m%d%H%M"),
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

        # Note: xml_str is currently not stored (same behaviour as previous util)
        return self.insert(payload)

    def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        resp = self.client.table("nfe").select(
            "*").eq("id", record_id).execute()
        if not resp.data:
            return None
        return resp.data[0]

    def update(self, record_id: str, update_payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.client.table("nfe").update(
            update_payload).eq("id", record_id).execute()
        if not resp.data:
            raise Exception("Falha ao atualizar NF-e no Supabase")
        return resp.data[0]

    def update_status(self, record_id: str, status: str, payload_retorno: Optional[Any] = None, expected_current_status: Optional[str] = None) -> Optional[Dict[str, Any]]:
        payload = {"status": status, "atualizado_em": datetime.now(
            timezone.utc).isoformat()}
        if payload_retorno is not None:
            payload["payload_retorno"] = payload_retorno

        # Perform conditional update when expected_current_status is provided
        query = self.client.table("nfe").update(payload).eq("id", record_id)
        if expected_current_status is not None:
            query = query.eq("status", expected_current_status)

        resp = query.execute()

        # If no rows were updated, return None (caller can decide how to proceed)
        if not resp.data:
            return None
        return resp.data[0]

    def mark_error(self, record_id: str, error: Any) -> Dict[str, Any]:
        return self.update_status(record_id, "ERRO", {"error": str(error)})


__all__ = ["NFeService", "NFeServiceProtocol"]
