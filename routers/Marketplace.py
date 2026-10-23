from fastapi import APIRouter, Form , Depends , Path , HTTPException , status , Request , Response , File, UploadFile
from database.database import get_db
from database.models import User , Business , Services , ServiceRequest

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from redis_client import redis
from datetime import datetime , timedelta , timezone

from schemas.Marketplace import NewRequest
from services.user_auth import get_current_user_payload

router=APIRouter(tags=["Marketplace"])

@router.get("/Marketplace")
async def marketplace__get_all(payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    db_business= await db.scalars(select(Business))
    db_business_list=db_business.all()
    display_list=[
        {
            "id":business.id,
            "name":business.business_name,
            "title":business.title,
            "thumbnail":business.thumbnail
        }
        for business in db_business_list
    ]
    return display_list

@router.get("/Marketplace/Business/{id}")
async def marketplace_business__get_one(id:int,payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    db_business= await db.get(Business,id)
    if not db_business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Business Found")
    db_services= await db.scalars(select(Services).where(Services.business_id == id))
    db_business_list=db_services.all()
    display_list={
        "id":db_business.id,
        "name":db_business.business_name,
        "title":db_business.title,
        "thumbnail":db_business.thumbnail,
        "services":[
            {
                "id":service.id,
                "name":service.name,
                "description":service.description,
                "pricing_type":service.pricing_type,
                "unit":service.unit,
                "price":service.price
            }
            for service in db_business_list
        ]
    }
    return display_list

@router.post("/Marketplace/Business/{id}/request")
async def marketplace_business__request(id:int,new_request:NewRequest,payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    user_id=int(payload.get("sub"))

    db_business= await db.get(Business,id)
    if not db_business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Business Found")
    try:
        service_ids=[ int(i.strip()) for i in new_request.services.split(",")]
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Service IDs must be comma-separated integer.")
    db_services= await db.scalars(select(Services).where(Services.business_id == db_business.id, Services.id.in_(service_ids)))
    db_services_list=db_services.all()
    if not db_services_list or len(db_services_list) != len(service_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="One or more Services Found")

    db_new= ServiceRequest(
        business_id=id,
        user_id=user_id,
        services=new_request.services,
        work=new_request.work,
        notes=new_request.notes,
        status="new request",
        create_at=datetime.now(timezone.utc),
        update_at=datetime.now(timezone.utc),
    )

    db.add(db_new)
    try:
        await db.commit()
        return {
            "message":"Request was send. "
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is down.")

