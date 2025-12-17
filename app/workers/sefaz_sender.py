from app.core.sefaz import SefazAPI
from app.models.nfe import NFe
from app.services.wsdl_urls.wsdl_urls import WSDLProvider
from app.services.xml_signer.xml_signer_mock import XMLSignerMock
from app.common.patterns.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, retry_with_circuit_breaker
from app.common.patterns.retry import ExponentialBackoff

import logging

logger = logging.getLogger(__name__)

class SefazSender:
    """Envia NF-e para a SEFAZ"""
    
    def __init__(self):
        self.sefaz_api = SefazAPI(XMLSignerMock(), WSDLProvider())
        self.circuit_breaker = CircuitBreaker(
            CircuitBreakerConfig(failure_threshold=5)
        )
        self.backoff = ExponentialBackoff(
            initial_delay=1.0, max_delay=10.0, max_attemps=4, jitter=True
        )
    
    async def enviar(self, xml_str: str, record: dict) -> dict:
        """Envia XML para SEFAZ com retry e circuit breaker"""
        payload_envio = record.get("payload_envio") or {}
        nfe = NFe(**payload_envio)
        
        async def operation():
            result = self.sefaz_api.send_nfe(xml_str, nfe.uf_emitente)
            if hasattr(result, "__await__"):
                return await result
            return result
        
        try:
            return await retry_with_circuit_breaker(
                operation, 
                self.circuit_breaker, 
                self.backoff
            )
        except Exception as e:
            logger.exception("Erro ao enviar para SEFAZ: %s", e)
            raise