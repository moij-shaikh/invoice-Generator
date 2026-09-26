from fastapi import APIRouter, Request, Response,Path,status,HTTPException, Form , Depends

from database.models import Job , Services , Client , Business , JobServices , Quotation , Invoice
from database.database import get_db
from sqlalchemy import select 
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_auth import get_current_user_payload
# 
from schemas.invoice import UpdateInvoice
from datetime import datetime, timezone

router=APIRouter()

@router.post("/invoice/{quotation_id}")
async def invoice__new(status:str=Form(),quotation_id:int=Path(ge=0),db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_quotation= await db.scalar(select(Quotation).join(Business, Business.id == Quotation.business_id).where(Quotation.id == quotation_id , Business.user_id ==user_id).with_for_update())
    if not db_quotation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Quotation Found. ")

    last_number= await db.scalar(select(Invoice.invoice_number).join(
        Quotation, Quotation.id == Invoice.quotation_id
    ).join(
        Business,Business.id == Quotation.business_id).where(
        Business.user_id == user_id)
        .order_by(Invoice.invoice_number.desc())
        )
    if not last_number:
        invoice_number=1
    else:
        invoice_number=last_number+1
    new_invoice=Invoice(
        quotation_id = quotation_id,
        invoice_number=invoice_number,
        created_at=datetime.now(timezone.utc),
        status=status
    )
    try: 
        db.add(new_invoice)
        await db.commit()
        return{
            "message":"Invoice was generated. "
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is Down.")
        
@router.get("/invoice")
async def invoice__display_all(db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_invoices= await db.scalars(select(Invoice).join(Invoice.quotation).join(Quotation.business).where(Business.user_id == user_id))
    db_invoices_list=db_invoices.all()
    if not db_invoices_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Invoice Found. ")
    return db_invoices_list

@router.get("/invoice/{id}")
async def invoice__display_ById(id:int=Path(ge=0),db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_invoice= await db.scalar(select(Invoice).join(Invoice.quotation).join(Quotation.business).where(Business.user_id == user_id, Invoice.id == id))
    if not db_invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Invoice Found. ")
    return db_invoice


@router.delete("/invoice/{id}")
async def invoice__delete(id:int=Path(ge=0),db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_invoice= await db.scalar(select(Invoice).join(Invoice.quotation).join(Quotation.business).where(Business.user_id == user_id, Invoice.id == id))
    if not db_invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Invoice Found. ")
    try:
        await db.delete(db_invoice)
        await db.commit()
        return db_invoice
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is Down.")

@router.patch("/invoice/{id}")
async def invoice__update(new_data:UpdateInvoice,id:int=Path(ge=0),payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    user_id=int(payload.get("sub"))
    db_invoice= await db.scalar(select(Invoice).join(Invoice.quotation).join(Quotation.business).where(Business.user_id == user_id, Invoice.id == id))
    if not db_invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Invoice Found. ")
    filled_data=new_data.model_dump(exclude_none=True)
    for field , value in filled_data.items():
        setattr(db_invoice,field,value)
    try:
        await db.commit()
        return db_invoice
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is Down.")