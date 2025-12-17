import os
import logging
from datetime import datetime, timezone

import httpx

from app.common.patterns.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, retry_with_circuit_breaker
from app.common.patterns.retry import ExponentialBackoff
from app.core.sefaz import SefazAPI
from app.services.wsdl_urls.wsdl_urls import WSDLProvider
from app.enums.nfe_status import StatusNFe
from app.models.nfe import NFe
from app.services.xml_signer.xml_signer_mock import XMLSignerMock
from app.utils.build_nfe_xml import build_nfe_xml
import json
import hmac
import hashlib
from app.services.nfe.nfe import NFeServiceProtocol

logger = logging.getLogger(__name__)

# Circuit breaker / backoff config for external calls (SEFAZ / client webhook)
_sefaz_cb = CircuitBreaker(CircuitBreakerConfig(failure_threshold=5))
_default_backoff = ExponentialBackoff(
    initial_delay=1.0, max_delay=10.0, max_attemps=4, jitter=True)


async def _send_to_sefaz(xml_str: str, uf: str) -> dict:
    """Enviar XML para a API SOAP da SEFAZ."""
    
    sefaz_api = SefazAPI(XMLSignerMock(), WSDLProvider())
    
    result = sefaz_api.send_nfe(xml_str, uf)
    if hasattr(result, "__await__"):
        return await result
    return result


async def _notify_client_webhook(record: dict, status: str) -> None:
    payload_envio = record.get("payload_envio") or {}
    url = None

    client_info = payload_envio.get("client") if isinstance(
        payload_envio, dict) else None
    if client_info and isinstance(client_info, dict):
        url = client_info.get("webhook_url")

    if not url:
        url = os.getenv("CLIENT_WEBHOOK_URL")

    if not url:
        logger.debug(
            "Nenhuma URL de webhook do cliente configurada; skip notifying")
        return

    body = {
        "id": record.get("id"),
        "ref": record.get("ref"),
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    async def operation():
        async with httpx.AsyncClient(timeout=10.0) as client:
            SECRET = os.getenv("CLIENT_WEBHOOK_SECRET", "default-secret")
            payload_bytes = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            signature = hmac.new(SECRET.encode(), payload_bytes, hashlib.sha256).hexdigest()
            resp = await client.post(url, json=body, headers={"Content-Type": "application/json", "x-webhook-signature": signature})
            resp.raise_for_status()
            return resp

    try:
        await retry_with_circuit_breaker(operation, _sefaz_cb, _default_backoff)
    except Exception as e:
        logger.exception("Falha ao notificar webhook do cliente: %s", e)


async def processar_nfe_worker(record_id: str, nfe_service: NFeServiceProtocol) -> None:
    try:
        record = nfe_service.get_by_id(record_id)

        if not record:
            logger.warning("Registro NF-e não encontrado: %s", record_id)
            return 

        current_status = record.get("status")

        if current_status not in (StatusNFe.CRIADA.value, StatusNFe.PROCESSANDO.value):
            logger.info(
                "Registro %s com status %s - não será processado", record_id, current_status)
            return

        updated = nfe_service.update_status(
            record_id,
            StatusNFe.PROCESSANDO.value,
            expected_current_status=StatusNFe.CRIADA.value,
        )
        
        if not updated:
            logger.info("Registro %s já está sendo processado por outro worker; skipping", record_id)
            return

        await _notify_client_webhook(record, StatusNFe.PROCESSANDO.value)

        # 3) Construir o objeto NFe e gerar XML (se necessário)
        payload_envio = record.get("payload_envio") or {}
        nfe = NFe(**payload_envio)
        xml_str = build_nfe_xml(nfe)

        # 4) Enviar para a SEFAZ (usa `sefaz_api` injetado se fornecido)
        try:
            sefaz_result = await _send_to_sefaz(xml_str, nfe.uf_emitente)
        except Exception as e:
            logger.exception("Erro ao enviar para SEFAZ: %s", e)
            nfe_service.mark_error(record_id, e)

            await _notify_client_webhook(record, StatusNFe.ERRO.value)
            return
        
        # 5) Atualizar o registro no Supabase com o resultado da SEFAZ
        payload_retorno = sefaz_result
        new_status = StatusNFe.REJEITADA.value

        if isinstance(sefaz_result, dict) and sefaz_result.get("status") == StatusNFe.AUTORIZADA.value:
            new_status = StatusNFe.AUTORIZADA.value

        update_payload = {
            "status": new_status,
            "payload_retorno": payload_retorno,
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
        }

        if isinstance(sefaz_result, dict):
            for k in ("chave_nfe", "numero", "serie", "xml_url", "danfe_url", "autorizado_em"):
                if k in sefaz_result:
                    update_payload[k] = sefaz_result[k]

        nfe_service.update(record_id, update_payload)

        # 6) Notificar cliente do novo status
        record.update(update_payload)
        
        await _notify_client_webhook(record, new_status)

    except Exception as e:
        logger.exception(
            "Erro inesperado no worker processar_nfe_worker: %s", e)
        try:
            nfe_service.mark_error(record_id, e)
        except Exception:
            logger.exception(
                "Falha ao atualizar registro de erro no Supabase para %s", record_id)
