from fastapi import FastAPI, Body, HTTPException, Response
from app.models.nfe import NFe
from app.utils.build_nfe_xml import build_nfe_xml
from app.utils.validar_nfe import validar_nfe  

app = FastAPI()


@app.post(
    "/nfe/json-para-xml",
    response_class=Response,
    responses={
        200: {
            "content": {"application/xml": {}},
            "description": "XML da NF-e gerado com sucesso"
        }
    },
)
async def json_para_xml(nfe: NFe = Body(...)):
    try:
        validar_nfe(nfe)

        xml_str = build_nfe_xml(nfe)

        return Response(
            content=xml_str,
            media_type="application/xml"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar XML da NF-e: {str(e)}"
        )
