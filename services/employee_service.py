from model.employee import Employee
from pathlib import Path
import csv
from datetime import date

PASTA_DADOS = Path("data")
PASTA_DADOS.mkdir(exist_ok=True)

ARQUIVO_EMPLOYEE = PASTA_DADOS / "employee.csv"

def read_csv_employee():
    employees = []
    if ARQUIVO_EMPLOYEE.exists() and ARQUIVO_EMPLOYEE.stat().st_size > 0:
        with open(ARQUIVO_EMPLOYEE, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                employees.append(Employee(
                    id=int(row["id"]),
                    id_department=int(row["id_department"]),
                    name=row["name"],
                    cpf=row["cpf"],
                    position=row["position"],
                    admission_date=date.fromisoformat(row["admission_date"]),
                    id_crud_verify=row["id_crud_verify"],
                ))
    return employees


def write_csv_employee(employees):
    with open(ARQUIVO_EMPLOYEE, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "id", "id_department", "name", "cpf", 
            "position", "admission_date", "id_crud_verify"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for e in employees:
            writer.writerow(e.model_dump())


def get_all_employees_ids():
    return [emp.id for emp in read_csv_employee()]
