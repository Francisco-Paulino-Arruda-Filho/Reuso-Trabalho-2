from fastapi import HTTPException
from typing import List
from fastapi import APIRouter
from model.pay_roll import PayRoll
from logger import logger
from services.pay_roll_service import read_csv_pay_roll, write_csv_pay_roll, ARQUIVO_PAY_ROLLS
from services.employee_service import get_all_employees_ids
from fastapi.responses import Response
from io import BytesIO, StringIO
import zipfile
import csv
from hashlib import sha256
import xml.etree.ElementTree as ET

router = APIRouter(prefix="/pay_rolls", tags=["Folha de Pagamentos"])

@router.get("/quantity")
def count_pay_rolls():
    count = len(read_csv_pay_roll())

    logger.info("Retornando quantidade de folha de pagamentos")

    return { "quantidade": count }

@router.get("/SHA256")
def calculate_hash_256():
    with open(ARQUIVO_PAY_ROLLS, "rb") as file:
        data = file.read()
        encrypted_data = sha256(data).hexdigest()

        logger.info("Calculando o hash de folha de pagamentos")

        return { "hash_sha_256": encrypted_data}

@router.get("/xml")
def convert_csv_to_xml():
    root = ET.Element("pay_rolls")

    for row in read_csv_pay_roll():
        pay_roll = ET.SubElement(root, "pay_roll")

        for key, pr in row.dict().items():
            field = ET.SubElement(pay_roll, key)
            field.text = str(pr)

    xml_bytes_io = BytesIO()
    tree = ET.ElementTree(root)
    tree.write(xml_bytes_io, encoding="UTF-8", xml_declaration=True)
    xml_string = xml_bytes_io.getvalue()

    logger.info("Convertendo para xml o csv de folha de pagamentos")

    return Response(
        content=xml_string,
        media_type="aplication/xml"
    )

@router.post("/pay_roll", response_model=PayRoll)
def create_pay_roll(pay_roll: PayRoll):
    pay_rolls = read_csv_pay_roll()

    for employee_id in pay_roll.employees:
        if not any(employee_id == emp_id for emp_id in get_all_employees_ids()):
            raise HTTPException(status_code=404, detail="Funcionário não encontrado")

    pay_rolls.append(pay_roll)
    write_csv_pay_roll(pay_rolls)
    logger.info(f"Folha de pagamento com ID {pay_roll.id} adicionada com sucesso")
    return pay_roll

@router.get("/", response_model=List[PayRoll])
def get_pay_rolls():
    logger.info("Retornando todas as folhas de pagamento")
    return read_csv_pay_roll()

@router.put("/{pay_roll_id}", response_model=PayRoll)
def update_pay_roll(pay_roll_id: int, pay_roll: PayRoll):
    pay_rolls = read_csv_pay_roll()

    for employee_id in pay_roll.employees:
        if not any(employee_id == emp_id for emp_id in get_all_employees_ids()):
            raise HTTPException(status_code=404, detail="Funcionário não encontrado")

    for i, pr in enumerate(pay_rolls):
        if pr.id == pay_roll_id:
            pay_rolls[i] = pay_roll
            write_csv_pay_roll(pay_rolls)
            logger.info(f"Folha de Pagamento com ID {pay_roll_id} atualizada com sucesso")
            return pay_roll
    raise HTTPException(status_code=404, detail="Folha de Pagamento não encontrada")

@router.delete("/{pay_roll_id}")
def delete_pay_roll(pay_roll_id: int):
    pay_rolls = read_csv_pay_roll()

    for i, pr in enumerate(pay_rolls):
        if pr.id == pay_roll_id:
            del pay_rolls[i]
            write_csv_pay_roll(pay_rolls)
            logger.info(f"Folha de pagamento com ID {pay_roll_id} deletada com sucesso")
            return {"message": "Folha de pagamento deletada com sucesso"}
    raise HTTPException(status_code=404, detail="Folha de pagamento não encontrada")

@router.get("/zip")
def get_pay_roll_zip():
    departments = read_csv_pay_roll()
    if not departments:
        raise HTTPException(status_code=404, detail="Nenhuma folha de pagamento encontrada")

    csv_string_io = StringIO()
    writer = csv.DictWriter(csv_string_io, fieldnames=departments[0].dict().keys())
    writer.writeheader()
    for dept in departments:
        writer.writerow(dept.dict())

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("pay_roll.csv", csv_string_io.getvalue())

    zip_buffer.seek(0)

    logger.info("pay_roll.csv convertido para .zip")

    return Response(
        content=zip_buffer.read(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=pay_roll.zip"}
    )

@router.get("/{pay_roll_id}", response_model=PayRoll)
def get_pay_roll(pay_roll_id: int):
    for pr in read_csv_pay_roll():
        if pr.id == pay_roll_id:
            logger.info(f"Retornando folha de pagamento com ID: {pay_roll_id}")
            return pr
    raise HTTPException(status_code=404, detail="Folha de Pagamento não encontrada")