from datetime import datetime, timezone
from app.enums.nfe_status import StatusNFe

class ResultProcessor:
    """Processa o resultado da SEFAZ e atualiza o registro"""
    
    def __init__(self, nfe_service, webhook_notifier):
        self.nfe_service = nfe_service
        self.webhook_notifier = webhook_notifier
    
    async def processar(self, record_id: str, record: dict, sefaz_result: dict) -> None:
        """Processa resultado da SEFAZ e atualiza registro"""
        # Determinar novo status
        novo_status = self._determinar_status(sefaz_result)
        
        # Construir payload de atualização
        update_payload = self._construir_update_payload(sefaz_result, novo_status)
        
        # Atualizar registro
        self.nfe_service.update(record_id, update_payload)
        
        # Atualizar record local para notificação
        record.update(update_payload)
        
        # Notificar cliente
        await self.webhook_notifier.notificar(record, novo_status)
    
    def _determinar_status(self, sefaz_result: dict) -> str:
        """Determina o novo status baseado no resultado da SEFAZ"""
        if isinstance(sefaz_result, dict) and \
           sefaz_result.get("status") == StatusNFe.AUTORIZADA.value:
            return StatusNFe.AUTORIZADA.value
        return StatusNFe.REJEITADA.value
    
    def _construir_update_payload(self, sefaz_result: dict, novo_status: str) -> dict:
        """Constrói o payload de atualização do registro"""
        update_payload = {
            "status": novo_status,
            "payload_retorno": sefaz_result,
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
        }
        
        # Copiar campos adicionais se existirem
        if isinstance(sefaz_result, dict):
            campos_extras = [
                "chave_nfe", "numero", "serie", 
                "xml_url", "danfe_url", "autorizado_em"
            ]
            for campo in campos_extras:
                if campo in sefaz_result:
                    update_payload[campo] = sefaz_result[campo]
        
        return update_payload