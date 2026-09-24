from pydantic import BaseModel , Field
from datetime import datetime , timezone

class Update(BaseModel):
    title:str|None=None
    work:str|None=None
    note:str|None=None
    start_at:datetime|None=None
    end_at:datetime|None=None
    job_status:str|None=None
    total_price:int|None=None