from pydantic import BaseModel

from enum import Enum

class QuotationStatus(str,Enum):
    QUOTATION="quotation"
    CANCEL="cancel"
    ACCEPTED="accepted"
    REJECTED="rejected"

class ShowAllQuotation(BaseModel):
    id:int
    client_id:int
    quotation_status:QuotationStatus
    job_id:int
    total:float

class ShowQuotation(BaseModel):
    id:int
    client_id:int
    quotation_status:QuotationStatus
    job_id:int
    total:float

class NewQuotation(BaseModel):
    discount:int | None =None
    quotation_status:QuotationStatus
    client_id:int
    job_id:int

class UpdateQuotation(BaseModel):
    discount:int | None =None
    quotation_status:QuotationStatus
