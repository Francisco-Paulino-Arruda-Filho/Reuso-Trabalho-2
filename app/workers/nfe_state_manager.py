
from typing import Optional

import logging

from app.enums.nfe_status import StatusNFe

logger = logging.getLogger(__name__)

class NFeStateManager:
    """Gerencia transições de estado da NF-e"""
    
    def __init__(self, nfe_service, webhook_notifier):
        self.nfe_service = nfe_service
        self.webhook_notifier = webhook_notifier
    
    async def preparar_processamento(self, record_id: str) -> Optional[dict]:
        """Valida e prepara o registro para processamento"""
        record = await self.nfe_service.get_by_id(record_id)
        
        if not record:
            logger.warning("Registro NF-e não encontrado: %s", record_id)
            return None
        
        current_status = record.get("status")
        
        # Validar se pode ser processado
        if current_status not in (StatusNFe.CRIADA.value, StatusNFe.PROCESSANDO.value):
            logger.info("Registro %s com status %s - não será processado", 
                       record_id, current_status)
            return None
        
        # Tentar adquirir lock
        updated = await self.nfe_service.update_status(
            record_id,
            StatusNFe.PROCESSANDO.value,
            expected_current_status=StatusNFe.CRIADA.value,
        )
        
        if not updated:
            logger.info("Registro %s já está sendo processado; skipping", record_id)
            return None
        
        # Notificar início do processamento
        await self.webhook_notifier.notificar(record, StatusNFe.PROCESSANDO.value)
        
        return record
    
    async def marcar_erro(self, record_id: str, erro: Exception) -> None:
        """Marca o registro como erro"""
        try:
            await self.nfe_service.mark_error(record_id, erro)
            record = await self.nfe_service.get_by_id(record_id)
            if record:
                await self.webhook_notifier.notificar(record, StatusNFe.ERRO.value)
        except Exception:
            logger.exception("Falha ao marcar erro para %s", record_id)
