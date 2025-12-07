from model.department import Department
from pathlib import Path
import csv

PASTA_DADOS = Path("data")
PASTA_DADOS.mkdir(exist_ok=True)

ARQUIVO_DEPARTMENT = PASTA_DADOS / "department.csv"

def read_csv_department():
    departments = []
    if ARQUIVO_DEPARTMENT.exists() and ARQUIVO_DEPARTMENT.stat().st_size > 0:
        with open(ARQUIVO_DEPARTMENT, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                departments.append(Department(
                    id=int(row["id"]),
                    name=row["name"],
                    manager=row["manager"],
                    location=row["location"],
                    number_of_employees=int(row["number_of_employees"]),
                    id_crud_verify=row["id_crud_verify"],   
                ))
    return departments


def write_csv_department(departments):
    with open(ARQUIVO_DEPARTMENT, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "id",
            "name",
            "manager",
            "location",
            "number_of_employees",
            "id_crud_verify"  
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for d in departments:
            writer.writerow(d.model_dump())
