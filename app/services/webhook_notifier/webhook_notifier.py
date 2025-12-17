import os
import json
import hmac
import hashlib
from datetime import datetime, timezone
import httpx
from app.common.patterns.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, retry_with_circuit_breaker, ExponentialBackoff
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class WebhookNotifier:
    """Notifica clientes via webhook"""
    
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            CircuitBreakerConfig(failure_threshold=5)
        )
        self.backoff = ExponentialBackoff(
            initial_delay=1.0, max_delay=10.0, max_attemps=4, jitter=True
        )
    
    async def notificar(self, record: dict, status: str) -> None:
        """Envia notificação para o webhook do cliente"""
        url = self._extrair_webhook_url(record)
        
        if not url:
            logger.debug("Nenhuma URL de webhook configurada; skip")
            return
        
        body = self._construir_payload(record, status)
        
        async def operation():
            return await self._enviar_webhook(url, body)
        
        try:
            await retry_with_circuit_breaker(
                operation, 
                self.circuit_breaker, 
                self.backoff
            )
        except Exception as e:
            logger.exception("Falha ao notificar webhook: %s", e)
    
    def _extrair_webhook_url(self, record: dict) -> Optional[str]:
        """Extrai URL do webhook do registro ou variável de ambiente"""
        payload_envio = record.get("payload_envio") or {}
        client_info = payload_envio.get("client") if isinstance(
            payload_envio, dict) else None
        
        if client_info and isinstance(client_info, dict):
            url = client_info.get("webhook_url")
            if url:
                return url
        
        return os.getenv("CLIENT_WEBHOOK_URL")
    
    def _construir_payload(self, record: dict, status: str) -> dict:
        """Constrói o payload da notificação"""
        return {
            "id": record.get("id"),
            "ref": record.get("ref"),
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    
    async def _enviar_webhook(self, url: str, body: dict) -> httpx.Response:
        """Envia requisição HTTP para o webhook"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            secret = os.getenv("CLIENT_WEBHOOK_SECRET", "default-secret")
            payload_bytes = json.dumps(
                body, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")
            signature = hmac.new(
                secret.encode(), payload_bytes, hashlib.sha256
            ).hexdigest()
            
            resp = await client.post(
                url, 
                json=body, 
                headers={
                    "Content-Type": "application/json",
                    "x-webhook-signature": signature
                }
            )
            resp.raise_for_status()
            return resp
