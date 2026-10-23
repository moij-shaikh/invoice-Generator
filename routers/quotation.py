from fastapi import APIRouter,status,HTTPException , Depends , Path

from database.models import Job, Business , Quotation, Invoice
from database.database import get_db
from sqlalchemy import select 
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_auth import get_current_user_payload
# 
from schemas.quotation import NewQuotation, UpdateQuotation , ShowAllQuotation , ShowQuotation, QuotationStatus
from datetime import datetime, timezone

router=APIRouter(tags=["Quotation"])

@router.post("/Quotation", status_code=status.HTTP_201_CREATED)
async def quotation__new(
    new_quotation:NewQuotation,
    payload:dict=Depends(get_current_user_payload),
    db:AsyncSession=Depends(get_db)
    ):
    user_id=int(payload.get("sub"))
    db_business= await db.scalar(select(Business).where(Business.user_id == user_id))
    if not db_business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Business Found. ")
    db_job= await db.scalar(select(Job).join(Business,Business.id == Job.business_id).where(
        Business.id == db_business.id,
        Job.client_id == new_quotation.client_id,
        Job.id == new_quotation.job_id
    ))
    if not db_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Jobs Found")
    if new_quotation.discount >= new_quotation.total:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Discount must be less than the total price.  ")
    db_quotation=Quotation(
        business_id=db_business.id,
        client_id = new_quotation.client_id,
        job_id = new_quotation.job_id,
        total=new_quotation.total,
        discount=new_quotation.discount,
        quotation_status=QuotationStatus.PENDING,
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
    return db_quotations_list


@router.get("/Quotation/{id}",response_model=ShowQuotation)
async def quotation__display_all(id:int=Path(gt=0),db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_quotations= await db.scalar(select(Quotation).join(Business,Business.id == Quotation.business_id).where(Business.user_id == user_id,Quotation.id ==id))
    if not db_quotations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Data Found")
    return db_quotations


@router.delete("/Quotation/{id}")
async def quotation__display_all(id:int=Path(gt=0),db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_quotations= await db.scalar(select(Quotation).join(Business,Business.id == Quotation.business_id).where(Business.user_id == user_id,Quotation.id ==id))
    if not db_quotations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Data Found")
    existing= await db.scalar(select(Invoice).join(Business).where(Invoice.quotation_id == db_quotations.id, Invoice.business_id ==db_quotations.business_id, Business.user_id == user_id ))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete a quotation that has an invoice.")
        
    try: 
        db_quotations.quotation_status= QuotationStatus.CANCEL
        db_quotations.update_at = datetime.now(timezone.utc)
        
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
    filled_data = updated_data.model_dump(exclude_unset=True)
    db_quotation= await db.scalar(select(Quotation).join(Business).where(Quotation.id ==id, Business.user_id == user_id))
    if not db_quotation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Data Found")
    if db_quotation.quotation_status == QuotationStatus.ACCEPTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quotation is already accepted.you can not change it. ")
    if db_quotation.quotation_status == QuotationStatus.CANCEL:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quotation is already cancelled.you can not change it. ")
    if db_quotation.quotation_status == QuotationStatus.REJECTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quotation is already rejected.you can not change it. ")
    existing = await db.scalar(select(Invoice).join(Business).where(Invoice.quotation_id == db_quotation.id,Business.user_id == user_id ))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An invoice is present for this quotation.you can not change it. ")
        
    new_total=(
        updated_data.total 
        if updated_data.total is not None
        else db_quotation.total
    )
    new_discount=(
        updated_data.discount
        if updated_data.discount is not None
        else db_quotation.discount
    )
    if new_total<=0 or new_discount < 0 or new_discount >= new_total:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Discount is greater than price. ")
    for field , value in filled_data.items():
        setattr(db_quotation , field, value)
    try:
        db_quotation.update_at = datetime.now(timezone.utc)
        await db.commit()
        return {
            "message":"Quotation is updated. "
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="DataBase is Down.")

