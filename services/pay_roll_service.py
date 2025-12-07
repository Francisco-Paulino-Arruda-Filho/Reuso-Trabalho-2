import csv
from pathlib import Path
from datetime import date
from model.pay_roll import PayRoll

PASTA_DADOS = Path("data")
PASTA_DADOS.mkdir(exist_ok=True)

ARQUIVO_PAY_ROLLS = PASTA_DADOS / "pay_roll.csv"

def read_csv_pay_roll():
    pay_rolls = []

    if ARQUIVO_PAY_ROLLS.exists() and ARQUIVO_PAY_ROLLS.stat().st_size > 0:
        with open(ARQUIVO_PAY_ROLLS, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            
            for pr in reader:
                pay_rolls.append(PayRoll(
                    id=int(pr["id"]),
                    discounts=float(pr["discounts"]),
                    net_salary=float(pr["net_salary"]),
                    gross_salary=float(pr["gross_salary"]),
                    reference_month=date.fromisoformat(pr["reference_month"]),
                    employees=[
                        int(e) for e in pr.get("employees", "").split(",") 
                        if e.isdigit()
                    ],
                    id_crud_verify=pr.get("id_crud_verify", ""),
                ))
    return pay_rolls


def write_csv_pay_roll(pay_rolls):
    with open(ARQUIVO_PAY_ROLLS, "w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "id",
            "discounts",
            "net_salary",
            "gross_salary",
            "reference_month",
            "employees",
            "id_crud_verify"
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for pr in pay_rolls:
            data = pr.model_dump()
            
            data["employees"] = ",".join(map(str, data["employees"]))
            
            writer.writerow(data)
