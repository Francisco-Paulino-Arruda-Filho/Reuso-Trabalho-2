from fastapi import Depends, FastAPI, Body, HTTPException, Response, Request, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timezone
from uuid import uuid4

from app.enums.nfe_status import StatusNFe
from app.models.nfe import NFe
from app.services.nfe.nfe import NFeService, NFeServiceProtocol
from app.utils.validar_nfe import validar_nfe
from app.utils.build_nfe_xml import build_nfe_xml
from app.common.patterns.rate_limit import check_rate_limit
from app.common.patterns.circuit_breaker import with_retry_and_circuit_breaker
from app.workers.processar_nfe_worker import processar_nfe_worker

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
    nfe: NFe = Body(...),
    nfe_service: NFeServiceProtocol = Depends(NFeService)
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

            # Add seconds + short uuid suffix to reduce collisions
            "ref": f"{agora.strftime('%y%m%d%H%M%S')}{uuid4().hex[:6]}",

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

        inserted = await nfe_service.insert(payload)

        if not inserted:
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


@app.post("/emitir-nfe", status_code=202)
async def emitir_nfe(
    request: Request,
    background_tasks: BackgroundTasks,
    nfe_service: NFeServiceProtocol = Depends(NFeService),
    nfe: NFe = Body(...)
):
    try:
        validar_nfe(nfe)
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Erro na validação: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Erro ao processar payload: {str(e)}")

    agora = datetime.now(timezone.utc)
    nfe_id = str(uuid4())
    record = {
        "id": nfe_id,
        "ref": f"{agora.strftime('%y%m%d%H%M%S')}{uuid4().hex[:6]}",
        "status": "CRIADA",
        "chave_nfe": None,
        "numero": None,
        "serie": None,
        "xml_url": None,
        "danfe_url": None,
        "payload_envio": jsonable_encoder(nfe),
        "payload_retorno": None,
        "ambiente": "producao",
        "data_emissao": (
            nfe.data_emissao.isoformat()
            if getattr(nfe, "data_emissao", None)
            else None
        ),
        "autorizado_em": None,
        "criado_em": agora.isoformat(),
        "atualizado_em": agora.isoformat(),
    }

    try:
        await nfe_service.insert(record)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao salvar NF-e: {str(e)}")

    background_tasks.add_task(processar_nfe_worker, record["id"], nfe_service)

    return {
        "success": True,
        "message": "NF-e recebida e em processamento",
        "data": {
            "id": nfe_id,
            "ref": record["ref"],
            "status": StatusNFe.CRIADA,
            "criado_em": agora.isoformat()
        }
    }

@app.get("/get_all_nfes")
async def get_all_nfes(
    nfe_service: NFeServiceProtocol = Depends(NFeService)
):
    try:
        nfe_records = nfe_service.get_all()
        return {
            "success": True,
            "data": nfe_records
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao buscar NF-es: {str(e)}")

@app.get("/get_nfe/{nfe_id}")
async def get_nfe(
    nfe_id: str,
    nfe_service: NFeServiceProtocol = Depends(NFeService)
):
    try:
        nfe_record = await nfe_service.get_by_id(nfe_id)
        if not nfe_record:
            raise HTTPException(status_code=404, detail="NF-e não encontrada")

        return {
            "success": True,
            "data": nfe_record
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao buscar NF-e: {str(e)}")