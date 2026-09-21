from fastapi import APIRouter, Request, Response,Path,status,HTTPException, Form

from database.models import Job , Services , Client , Business
from database.database import get_db
from sqlalchemy import select 
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from services.user_auth import get_current_user_payload

from datetime import datetime, timezone

router=APIRouter()

@router.post("/job")
async def job__new(
    client_id:int=Form(...),
    services_id:list[int]=Form(...),
    title:str=Form(...),
    work:str=Form(...),
    note:str=Form(...)
)