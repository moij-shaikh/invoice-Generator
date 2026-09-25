from fastapi import APIRouter, Request, Response,Path,status,HTTPException, Form , Depends

from database.models import Job , Services , Client , Business , JobServices
from database.database import get_db
from sqlalchemy import select 
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_auth import get_current_user_payload

from schemas.services import NewService, UpdateService
from datetime import datetime, timezone

router= APIRouter()

@router.get("/Services")
async def services__display_all(db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_services= await db.scalars(select(Services).join(Business,Services.business_id == Business.id).where(Business.user_id == user_id))
    db_services_list=db_services.all()
    if not db_services_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Services Found. ")
    return db_services_list
@router.get("/Services/{id}")
async def services__display_all(id:int,db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_service= await db.scalar(select(Services).join(Business,Services.business_id == Business.id).where(Business.user_id == user_id,Services.id ==id))
    if not db_service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Services Found. ")
    return db_service

@router.delete("/Services/{id}")
async def services__display_all(id:int,db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_service= await db.scalar(select(Services).join(Business,Services.business_id == Business.id).where(Business.user_id == user_id,Services.id ==id))
    if not db_service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Services Found. ")
    try:
        await db.delete(db_service)
        await db.commit()
        return db_service
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="DB is Down.")

@router.post("/Services")
async def services__new(new_service:NewService,db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))    
    db_business= await db.scalar(select(Business).where(Business.user_id == user_id))
    if not db_business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Business Found. ")
    new=Services(
        name=new_service.name,
        pricing_type=new_service.pricing_type,
        price=new_service.price,
        description=new_service.description,
        unit=new_service.unit,
        gst_percentage=new_service.gst_percentage,
        is_active=new_service.is_active,
        business_id=db_business.id,
        create_at=datetime.now(timezone.utc),
        update_at=datetime.now(timezone.utc)
    )
    try:
        db.add(new)
        await db.commit()
        return{
            "message":"New Service is Added. "
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="DB is Down.")

@router.patch("/Services/{id}")
async def services__update(update_services:UpdateService,db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    filled_data=update_services.model_dump(exclude_none=True)
    db_service= await db.scalar(select(Services).join(Business,Business.id == Services.business_id).where(Business.user_id == user_id, Services.id == id))
    if not db_service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Service Found. ")
    for field , value in filled_data.items():
        setattr(db_service,field , value)
    try:
        db_service.update_at=datetime.now(timezone.utc)
        await db.commit()
        return{
            "message":"New Service is Added. "
            }
    except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="DB is Down.")

