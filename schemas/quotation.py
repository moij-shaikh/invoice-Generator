from pydantic import BaseModel , Field, ConfigDict

from enum import Enum

class QuotationStatus(str,Enum):
    PENDING="pending"
    CANCEL="cancel"
    ACCEPTED="accepted"
    REJECTED="rejected"

class ShowAllQuotation(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int
    client_id:int
    quotation_status:QuotationStatus
    job_id:int
    discount: float
    

class ShowQuotation(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int
    client_id:int
    quotation_status:QuotationStatus
    discount: float
    job_id:int
    total:float

class NewQuotation(BaseModel):
    discount:int =Field(default=0,ge=0)
    client_id:int = Field(gt=0)
    job_id:int= Field(gt=0)

class UpdateQuotation(BaseModel):
    total:float | None=Field( default=None , gt=0)
    discount:float | None =Field(default=None, ge=0)
    quotation_status:QuotationStatus| None =None
