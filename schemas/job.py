from pydantic import BaseModel , Field
from datetime import datetime , timezone

from enum import Enum

class JobStatus(str, Enum):
    WORKING="working"
    CANCEL="cancel"
    DONE="done"
    REJECTED="rejected"
    PENDING="pending"

    
class JobServiceInput(BaseModel):
    service_id: int = Field(gt=0)
    quantity: float = Field(gt=0)

class NewJob(BaseModel):
    client_id:int = Field(gt=0)
    services:list[JobServiceInput]
    title:str
    work:str
    note:str
    start_at:datetime
    end_at:datetime

class Update(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    work: str | None = Field(default=None, min_length=1)
    note: str | None = Field(default=None, min_length=1)
    
    start_at:datetime|None=None
    end_at:datetime|None=None
    
    job_status:JobStatus|None=None