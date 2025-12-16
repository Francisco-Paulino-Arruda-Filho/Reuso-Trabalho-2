import os
import logging
from datetime import datetime, timezone

import httpx

from app.common.patterns.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, retry_with_circuit_breaker
from app.common.patterns.retry import ExponentialBackoff
from app.core.sefaz import SefazAPI
from app.core.wsdl_urls import WSDLProvider
from app.core.xml_signer_mock import XMLSignerMock
from app.enums.nfe_status import StatusNFe
from app.enums.nfe_status import StatusNFe
from app.infra.supabase_client import supabase
from app.models.nfe import NFe
from app.utils.build_nfe_xml import build_nfe_xml

logger = logging.getLogger(__name__)

# Circuit breaker / backoff config for external calls (SEFAZ / client webhook)
_sefaz_cb = CircuitBreaker(CircuitBreakerConfig(failure_threshold=5))
_default_backoff = ExponentialBackoff(
    initial_delay=1.0, max_delay=10.0, max_attemps=4, jitter=True)


async def _send_to_sefaz(xml_str: str, uf: str) -> dict:
    """Enviar XML para a API SOAP da SEFAZ.

    Retorna o JSON da resposta (ou lança exceção em falha).
    Use variáveis de ambiente:
    - SEFAZ_API_URL
    - SEFAZ_API_KEY (opcional)
    """
    sefazAPI = SefazAPI(XMLSignerMock(), WSDLProvider())

    return sefazAPI.send_nfe(xml_str, uf)


async def _notify_client_webhook(record: dict, status: str) -> None:
    """Notifica cliente com status via webhook.

    Procura pela URL no payload (`payload_envio.client.webhook_url`) e, se não houver, cai em CLIENT_WEBHOOK_URL env.
    """
    payload_envio = record.get("payload_envio") or {}
    url = None

    # Exemplo: payload_envio pode ter estrutura com url do cliente
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
            resp = await client.post(url, json=body, headers={"Content-Type": "application/json"})
            resp.raise_for_status()
            return resp

    try:
        await retry_with_circuit_breaker(operation, _sefaz_cb, _default_backoff)
    except Exception as e:
        logger.exception("Falha ao notificar webhook do cliente: %s", e)


async def processar_nfe_worker(record_id: str) -> None:
    """Worker que processa a NF-e em background:

    - Busca registro no Supabase
    - Marca como EM_PROCESSAMENTO
    - Gera XML (novamente) e envia para SEFAZ
    - Atualiza registro com resposta (payload_retorno, chave/numero/serie, status, URLs)
    - Notifica cliente via webhook
    """
    try:
        # 1) Buscar registro
        resp = supabase.table("nfe").select("*").eq("id", record_id).execute()

        if not resp.data:
            logger.warning("Registro NF-e não encontrado: %s", record_id)
            return

        record = resp.data[0]
        current_status = record.get("status")

        if current_status not in (StatusNFe.CRIADA.value, StatusNFe.PROCESSANDO.value):
            logger.info(
                "Registro %s com status %s - não será processado", record_id, current_status)
            return

        # 2) Atualizar status para EM_PROCESSAMENTO
        updated_at = datetime.now(timezone.utc).isoformat()
        supabase.table("nfe").update(
            {"status": StatusNFe.PROCESSANDO.value, "atualizado_em": updated_at}).eq("id", record_id).execute()

        # 3) Construir o objeto NFe e gerar XML (se necessário)
        payload_envio = record.get("payload_envio") or {}
        nfe = NFe(**payload_envio)
        xml_str = build_nfe_xml(nfe)

        # 4) Enviar para a SEFAZ
        try:
            sefaz_result = await _send_to_sefaz(xml_str, nfe.uf_emitente)
        except Exception as e:
            # Atualiza DB com erro e notifica (status de erro previsto: 'ERRO')
            logger.exception("Erro ao enviar para SEFAZ: %s", e)
            supabase.table("nfe").update({
                "status": StatusNFe.ERRO.value,
                "payload_retorno": {"error": str(e)},
                "atualizado_em": datetime.now(timezone.utc).isoformat(),
            }).eq("id", record_id).execute()

            # Notificar cliente de erro é opcional
            await _notify_client_webhook(record, StatusNFe.ERRO.value)
            return

        # 5) Processar resposta da SEFAZ e atualizar registro
        # NOTE: estrutura do `sefaz_result` depende da API real da SEFAZ
        payload_retorno = sefaz_result
        new_status = StatusNFe.REJEITADA.value

        # Exemplo de interpretação: se a resposta tem 'status' == 'AUTORIZADA'
        if isinstance(sefaz_result, dict) and sefaz_result.get("status") == StatusNFe.AUTORIZADA.value:
            new_status = StatusNFe.AUTORIZADA.value

        update_payload = {
            "status": new_status,
            "payload_retorno": payload_retorno,
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
        }

        # Se a SEFAZ retornou campos, atualizar também
        if isinstance(sefaz_result, dict):
            for k in ("chave_nfe", "numero", "serie", "xml_url", "danfe_url", "autorizado_em"):
                if k in sefaz_result:
                    update_payload[k] = sefaz_result[k]

        supabase.table("nfe").update(update_payload).eq(
            "id", record_id).execute()

        # 6) Notificar cliente do novo status
        # Atualiza `record` para enviar dados corretos
        record.update(update_payload)
        await _notify_client_webhook(record, new_status)

    except Exception as e:
        logger.exception(
            "Erro inesperado no worker processar_nfe_worker: %s", e)
        # Tentativa de marcar erro genérico no DB
        try:
            # Registrar erro no DB com status 'ERRO'
            supabase.table("nfe").update({
                "status": StatusNFe.ERRO.value,
                "payload_retorno": {"error": str(e)},
                "atualizado_em": datetime.now(timezone.utc).isoformat(),
            }).eq("id", record_id).execute()
        except Exception:
            logger.exception(
                "Falha ao atualizar registro de erro no Supabase para %s", record_id)
