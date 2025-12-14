from fastapi import FastAPI, Body, HTTPException, Response, Request
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timezone
from uuid import uuid4

from app.models.nfe import NFe
from app.utils.validar_nfe import validar_nfe
from app.utils.build_nfe_xml import build_nfe_xml
from app.infra.supabase_client import supabase
from app.core.rate_limit import check_rate_limit
from app.core.circuit_breaker import with_retry_and_circuit_breaker

app = FastAPI()


@app.post(
    "/nfe/json-para-xml",
    response_class=Response,
    responses={
        200: {"content": {"application/xml": {}}},
        400: {"description": "Erro de validação"},
        429: {"description": "Rate limit excedido"},
        500: {"description": "Erro interno"}
    }
)
@with_retry_and_circuit_breaker(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=10.0,
    jitter=True
)
async def json_para_xml(
    request: Request,
    nfe: NFe = Body(...)
):
    # ==========================
    # RATE LIMIT
    # ==========================
    rate_limit_response = await check_rate_limit(request)
    if rate_limit_response:
        return rate_limit_response

    try:
        validar_nfe(nfe)

        xml_str = build_nfe_xml(nfe)

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

            # JSONB seguro
            "payload_envio": jsonable_encoder(nfe),
            "payload_retorno": None,

            # varchar(10) SAFE
            "ambiente": "producao",

            # timestamptz SAFE
            "data_emissao": (
                nfe.data_emissao.isoformat()
                if getattr(nfe, "data_emissao", None)
                else None
            ),

            "autorizado_em": None,
            "criado_em": agora.isoformat(),
            "atualizado_em": agora.isoformat(),
        }

        response = supabase.table("nfe").insert(payload).execute()

        if not response.data:
            raise Exception("Falha ao persistir NF-e no Supabase")

        return Response(
            content=xml_str,
            media_type="application/xml"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar ou salvar NF-e: {str(e)}"
        )
