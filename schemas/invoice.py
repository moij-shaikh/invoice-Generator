from pydantic import BaseModel , Field, ConfigDict
from datetime import datetime 

from enum import Enum

class InvoiceStatus(str, Enum):
        UNPAID="unpaid"
        PAID="paid"
        PARTIAL_PAID="partial_paid"
        CANCELLED="cancelled"    

class NewInvoice(BaseModel):
    client_id:int = Field(gt=0)
    job_id:int= Field(gt=0)
    discount:float = Field(ge=0)
    start_date:datetime
    due_date:datetime
class UpdateInvoice(BaseModel):
    start_date:datetime | None =None
    due_date:datetime | None=None

class ShowAllInvoice(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    invoice_number:int
    client_id:int
    job_id:int
    total:float
    discount:float
    status:InvoiceStatus

class ShowInvoice(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    invoice_number:int
    client_id:int
    job_id:int
    total:float
    discount:float
    status:InvoiceStatus
    start_date:datetime
    due_date:datetime | None
    created_at:datetime
    updated_at:datetime | None