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
from app.services.webhook_notifier.webhook_notifier import WebhookNotifier
from app.services.nfe.nfe import NFeServiceProtocol

logger = logging.getLogger(__name__)

async def _send_to_sefaz(xml_str: str, uf: str) -> dict:
    """Enviar XML para a API SOAP da SEFAZ."""
    
    sefaz_api = SefazAPI(XMLSignerMock(), WSDLProvider())
    
    result = sefaz_api.send_nfe(xml_str, uf)
    if hasattr(result, "__await__"):
        return await result
    return result

async def processar_nfe_worker(record_id: str, nfe_service: NFeServiceProtocol) -> None:
    try:
        record = nfe_service.get_by_id(record_id)
        webhook_notifier = WebhookNotifier()

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

        await webhook_notifier.notificar(record, StatusNFe.PROCESSANDO.value)

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

            await webhook_notifier.notificar(record, StatusNFe.ERRO.value)
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
        
        await webhook_notifier.notificar(record, new_status)

    except Exception as e:
        logger.exception(
            "Erro inesperado no worker processar_nfe_worker: %s", e)
        try:
            nfe_service.mark_error(record_id, e)
        except Exception:
            logger.exception(
                "Falha ao atualizar registro de erro no Supabase para %s", record_id)
