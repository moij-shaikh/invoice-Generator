from pydantic import BaseModel , Field

from enum import Enum

class QuotationStatus(str,Enum):
    PENDING="pending"
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
    discount:int =Field(default=0,ge=0)
    client_id:int = Field(ge=0)
    job_id:int= Field(ge=0)
    total:int  = Field(ge=0)

class UpdateQuotation(BaseModel):
    total:int=Field(gt=0)
    discount:int | None =None
    quotation_status:QuotationStatus
