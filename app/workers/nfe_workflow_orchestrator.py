from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class ProcessamentoResult:
    """Resultado do processamento"""
    sucesso: bool
    novo_status: str
    payload_retorno: Optional[dict] = None
    erro: Optional[Exception] = None


class NFeWorkflowOrchestrator:
    """Orquestra o fluxo completo de processamento da NF-e"""

    def __init__(
        self,
        nfe_service,
        state_manager,
        xml_builder,
        sefaz_sender,
        webhook_notifier,
        result_processor
    ):
        self.nfe_service = nfe_service
        self.state_manager = state_manager
        self.xml_builder = xml_builder
        self.sefaz_sender = sefaz_sender
        self.webhook_notifier = webhook_notifier
        self.result_processor = result_processor

    async def processar(self, record_id: str) -> None:
        """Executa o workflow completo de processamento"""
        try:
            # 1. Validar e preparar processamento
            record = await self.state_manager.preparar_processamento(record_id)
            if not record:
                return

            # 2. Construir XML
            xml_str = self.xml_builder.build(record)

            # 3. Enviar para SEFAZ
            result = await self.sefaz_sender.enviar(xml_str, record)

            # 4. Processar resultado
            await self.result_processor.processar(record_id, record, result)

        except Exception as e:
            logger.exception("Erro no workflow para %s: %s", record_id, e)
            await self.state_manager.marcar_erro(record_id, e)
