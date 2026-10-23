from pydantic import BaseModel , Field
from datetime import datetime , timezone

from enum import Enum

class JobStatus(str, Enum):
    WORKING="working"
    CANCEL="cancel"
    DONE="done"
    REJECTED="rejected"
    PENDING="pending"
    QUOTATION="quotation"

class ShowAllJob(BaseModel):
    client_id:int
    title:str
    start_at:datetime
    end_at:datetime
    job_status:JobStatus
    total_price:float
    
class ShowJob(BaseModel):
    client_id:int
    services_ids_str:list[int]
    title:str
    work:str
    note:str
    start_at:datetime
    end_at:datetime
    job_status:JobStatus
    total_price:float
class NewJob(BaseModel):
    client_id:int
    services_ids_str:list[int]
    title:str
    work:str
    note:str
    start_at:datetime
    end_at:datetime
    job_status:JobStatus

class Update(BaseModel):
    title:str|None=None
    work:str|None=None
    note:str|None=None
    start_at:datetime|None=None
    end_at:datetime|None=None
    job_status:JobStatus|None=None
    total_price:float|None=None