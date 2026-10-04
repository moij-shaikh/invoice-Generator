from pydantic import BaseModel , Field
from datetime import datetime 

class NewInvoice(BaseModel):
    client_id:int
    job_id:int
    total:float
    discount:float
    status:str
    start_date:datetime
    due_date:datetime


class UpdateInvoice(BaseModel):
    status:str | None=None
    start_date:datetime | None =None
    due_date:datetime | None=None

class ShowAllInvoice(BaseModel):
    invoice_number:int
    client_id:int
    job_id:int
    total:float
    discount:float
    status:str

class ShowInvoice(BaseModel):
    invoice_number:int
    client_id:int
    job_id:int
    total:float
    discount:float
    status:str
    start_date:datetime
    due_date:datetime
    created_at:datetime
    updated_at:datetime