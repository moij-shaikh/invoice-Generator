from fastapi import APIRouter, Form , Depends , Path , HTTPException , status , Request , Response
from database.database import get_db
from database.models import User , Business

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession

from redis_client import redis
from datetime import datetime , timedelta , timezone

from schemas.business import NewBusiness , UpdateBusiness
from services.user_auth import get_current_user_payload
router=APIRouter()
@router.post("/business")
async def business__new(
    business_name:str=Form(),
    owner_name:str=Form(),
    email:str=Form(),
    phone:str=Form(),
    website:str=Form(),
    address_line1:str=Form(),
    address_line2:str=Form(),
    city:str=Form(),
    state:str=Form(),
    country:str=Form(),
    currency:str=Form(),
    gst_number:str=Form(),
    payload:dict=Depends(get_current_user_payload),
    db:AsyncSession=Depends(get_db)
    ):
    business = Business(
        user_id=payload.get("sub"),
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
    )
    # try:
    db.add(business)
    await db.commit()
    return{
        "message":f"{business_name} was successfully Registered."
    }
    # except SQLAlchemyError:
    #     await db.rollback()
    #     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database Is Down.")

@router.get("/business")
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
        await db.commit()
        return {
            "message":"New Values are set."
        }

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database Is Down.")

