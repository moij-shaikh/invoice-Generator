from pydantic import BaseModel , Field
from datetime import datetime 
class UpdateInvoice(BaseModel):
    status:str | None=None
    due_date:datetime | None=None