from fastapi import APIRouter, Form , Depends , Path , HTTPException , status , File, UploadFile
from database.database import get_db
from database.models import Business

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from redis_client import redis
from datetime import datetime, timezone

from schemas.business import GetBusiness , UpdateBusiness
from services.user_auth import get_current_user_payload
router=APIRouter(tags=["Business"])
@router.post("/business")
async def business__new(
    business_name:str=Form(),
    owner_name:str=Form(),
    email:str=Form(),
    phone:str=Form(),
    website:str|None=Form(default=None),
    address_line1:str=Form(),
    address_line2:str|None=Form(default=None),
    city:str=Form(),
    state:str=Form(),
    country:str=Form(),
    currency:str=Form(),
    gst_number:str|None=Form(default=None),
    title:str=Form(description="Shown to public"),
    thumbnail:UploadFile=File(None),
    
    payload:dict=Depends(get_current_user_payload),
    db:AsyncSession=Depends(get_db)
    ):
    user_id=int(payload.get("sub"))
    existing= await db.scalar(select(Business).where(Business.user_id==user_id))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="An Business is Already Registered.")
    file_path=None
    if thumbnail:
        file_path=f"uploads/business/file_{user_id}"
    business = Business(
        user_id=user_id,
        business_name=business_name,
        owner_name=owner_name,
        gst_number=gst_number,
        email=email,
        phone=phone,
        website=website,
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        state=state,
        country=country,
        currency=currency,
        create_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        title=title,
        thumbnail=file_path
    )
    try:
        db.add(business)
        await db.commit()
        return{
            "message":f"{business_name} was successfully Registered."
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database Is Down.")

@router.get("/business",response_model=list[GetBusiness])
async def user__get_business(db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_business= await db.scalars(select(Business).where(Business.user_id == user_id))
    db_business_list=db_business.all()
    if not db_business_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Business Found.")
    return db_business_list

@router.delete("/business/{id}")
async def business__delete(id:int=Path(gt=0),db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_business= await db.scalar(select(Business).where(Business.user_id == user_id , Business.id == id))
    if not db_business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Business Found.")
    try:
        await db.delete(db_business)
        await db.commit()
        return {
            "message":f"{db_business.business_name} was successfully deleted"
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database Is Down.")

@router.patch("/business/{id}")
async def business__update(id:int,user_data:UpdateBusiness,db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_business= await db.scalar(select(Business).where(Business.user_id==user_id , Business.id==id))
    data=user_data.model_dump(exclude_unset=True)
    for field , value in data.items():
        setattr(db_business,field,value)
    try:
        db_business.updated_at=datetime.now(timezone.utc)
        await db.commit()
        return {
            "message":f"{db_business.id} was updated."
        }

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database Is Down.")
