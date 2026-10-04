from fastapi import APIRouter,status,HTTPException , Depends

from database.models import Job, Business , Quotation
from database.database import get_db
from sqlalchemy import select 
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_auth import get_current_user_payload
# 
from schemas.quotation import NewQuotation, UpdateQuotation , ShowAllQuotation , ShowQuotation
from datetime import datetime, timezone

router=APIRouter(tags=["Quotation"])

@router.post("/Quotation")
async def quotation__new(
    new_quotation:NewQuotation,
    payload:dict=Depends(get_current_user_payload),
    db:AsyncSession=Depends(get_db)
    ):
    user_id=int(payload.get("sub"))
    db_business= await db.scalar(select(Business).where(Business.user_id == user_id))
    db_job= await db.scalar(select(Job).join(Business,Business.id == Job.business_id).where(
        Business.id == db_business.id,
        Job.client_id == new_quotation.client_id,
        Job.id == new_quotation.job_id
    ))
    if not db_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Jobs Found")
    db_quotation=Quotation(
        business_id=db_business.id,
        client_id = new_quotation.client_id,
        job_id = new_quotation.job_id,
        total=db_job.total_price,
        discount=new_quotation.discount,
        quotation_status=new_quotation.quotation_status,
        create_at=datetime.now(timezone.utc),
        update_at=datetime.now(timezone.utc)
    )
    try: 
        db.add(db_quotation)
        await db.commit()
        return{
            "message":"New Quotation is created. "
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="DataBase is Down.")

@router.get("/Quotation",response_model=list[ShowAllQuotation])
async def quotation__display_all(db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_quotations= await db.scalars(select(Quotation).join(Business,Business.id == Quotation.business_id).where(Business.user_id == user_id))
    db_quotations_list=db_quotations.all()
    if not db_quotations_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Data Found")
    return db_quotations_list


@router.get("/Quotation/{id}",response_model=ShowQuotation)
async def quotation__display_all(id:int,db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_quotations= await db.scalar(select(Quotation).join(Business,Business.id == Quotation.business_id).where(Business.user_id == user_id,Quotation.id ==id))
    if not db_quotations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Data Found")
    return db_quotations


@router.delete("/Quotation/{id}")
async def quotation__display_all(id:int,db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_quotations= await db.scalar(select(Quotation).join(Business,Business.id == Quotation.business_id).where(Business.user_id == user_id,Quotation.id ==id))
    if not db_quotations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Data Found")
    try: 
        await db.delete(db_quotations)
        await db.commit()
        return{
            "message":"Quotation was deleted. "
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="DataBase is Down.")


@router.patch("/Quotation/{id}")
async def Quotation__update(id:int,updated_data:UpdateQuotation,payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    user_id=int(payload.get("sub"))
    filled_data = updated_data.model_dump(exclude_none=True)
    db_quotation= await db.scalar(select(Quotation).join(Business).where(Quotation.id ==id, Business.user_id == user_id))
    if not db_quotation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Data Found")
    for field , value in filled_data.items():
        setattr(db_quotation , field, value)
    try:
        await db.commit()
        return {
            "message":"Quotation is updated. "
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="DataBase is Down.")

