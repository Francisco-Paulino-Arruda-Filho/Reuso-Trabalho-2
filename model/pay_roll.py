from datetime import date
from uuid import uuid4
from pydantic import BaseModel
from typing import List


class PayRollBase(BaseModel):
    discounts: float
    net_salary: float
    gross_salary: float
    reference_month: date
    employees: List[int]

class PayRollCreate(PayRollBase):
    pass

class PayRoll(PayRollBase):
    id: int
    id_crud_verify: str = uuid4().hex