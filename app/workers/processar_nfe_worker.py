import logging

from app.services.webhook_notifier.webhook_notifier import WebhookNotifier
from app.workers.nfe_state_manager import NFeStateManager
from app.workers.nfe_xml_builder import NFeXMLBuilder
from app.workers.sefaz_sender import SefazSender
from app.workers.result_processor import ResultProcessor
from app.workers.nfe_workflow_orchestrator import NFeWorkflowOrchestrator

logger = logging.getLogger(__name__)


async def processar_nfe_worker(record_id: str, nfe_service) -> None:
    """Worker principal - apenas orquestra o processamento"""
    
    webhook_notifier = WebhookNotifier()
    state_manager = NFeStateManager(nfe_service, webhook_notifier)
    xml_builder = NFeXMLBuilder()
    sefaz_sender = SefazSender()
    result_processor = ResultProcessor(nfe_service, webhook_notifier)

    orchestrator = NFeWorkflowOrchestrator(
        nfe_service=nfe_service,
        state_manager=state_manager,
        xml_builder=xml_builder,
        sefaz_sender=sefaz_sender,
        webhook_notifier=webhook_notifier,
        result_processor=result_processor
    )

    try:
        # Executar workflow
        await orchestrator.processar(record_id)
    except Exception as e:
        logger.exception(f"Erro no processamento da NFe {record_id}: {e}")
        await state_manager.update_nfe_status(record_id, 'ERRO')
        raise