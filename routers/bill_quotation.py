from fastapi import APIRouter, Request, Response,Path,status,HTTPException, Form , Depends

from database.models import Job , Services , Client , Business , JobServices , Quotation
from database.database import get_db
from sqlalchemy import select 
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_auth import get_current_user_payload

from datetime import datetime, timezone

router=APIRouter()

@router.post("/Quotation")
async def quotation__new(
    business_id:int=Form(ge=0),
    client_id:int=Form(ge=0),
    job_id:int=Form(ge=0),
    discount:int=Form(),
    payload:dict=Depends(get_current_user_payload),
    db:AsyncSession=Depends(get_db)
    ):
    user_id=int(payload.get("sub"))
    db_job= await db.scalar(select(Job).join(Business,Business.id == Job.business_id).where(
        Business.user_id == user_id,
        Business.id == business_id,
        Job.client_id == client_id,
        Job.id == job_id
    ))
    if not db_job:
        raise HTTPException(status_cde=status.HTTP_404_NOT_FOUND,detail="No Jobs Found")
    new_quotation=Quotation(
        user_id = user_id,
        business_id=business_id,
        client_id = client_id,
        job_id = job_id,
        total=db_job.total_price,
        discount=discount,
        status="quotation",
        create_at=datetime.now(timezone.utc),
        update_at=datetime.now(timezone.utc)
    )
    try: 
        db.add(new_quotation)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="DataBase is Down.")

@router.get("/Quotation")
async def quotation__display_all(db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_quotations= await db.scalars(select(Quotation).join(Business,Business.id == Quotation.business_id).where(Business.user_id == user_id))
    db_quotations_list=db_quotations.all()
    if not db_quotations_list:
        raise HTTPException(status_cde=status.HTTP_404_NOT_FOUND,detail="No Data Found")
    return db_quotations_list


@router.get("/Quotation/{id}")
async def quotation__display_all(id:int,db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_quotations= await db.scalar(select(Quotation).join(Business,Business.id == Quotation.business_id).where(Business.user_id == user_id,Quotation.id ==id))
    if not db_quotations:
        raise HTTPException(status_cde=status.HTTP_404_NOT_FOUND,detail="No Data Found")
    return db_quotations


@router.delete("/Quotation/{id}")
async def quotation__display_all(id:int,db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_quotations= await db.scalar(select(Quotation).join(Business,Business.id == Quotation.business_id).where(Business.user_id == user_id,Quotation.id ==id))
    if not db_quotations:
        raise HTTPException(status_cde=status.HTTP_404_NOT_FOUND,detail="No Data Found")
    try: 
        await db.delete(db_quotations)
        await db.commit()
        return{
            "message":"Quotation was deleted. "
        }
    except SQLAlchemyError:
        await db.rollback()

@router.patch("/Quotation/{id}")
async def Quotation__update(payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    user_id=int(payload.get("sub"))