from fastapi import APIRouter,Path,status,HTTPException, Form , Depends

from database.models import Business , Quotation , Invoice , Client , Job 
from database.database import get_db
from sqlalchemy import select 
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_auth import get_current_user_payload
# 
from schemas.invoice import NewInvoice,UpdateInvoice , ShowAllInvoice , ShowInvoice, InvoiceStatus
from schemas.quotation import QuotationStatus
from datetime import datetime, timezone

router=APIRouter(tags=["Invoice"])

@router.post("/invoice")
async def invoice__new(new_invoice:NewInvoice,db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_business= await db.scalar(select(Business).where(Business.user_id ==user_id).with_for_update())
    if not db_business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Business Found. ")
    db_client= await db.scalar(select(Client).where(Client.business_id ==  db_business.id, Client.id == new_invoice.client_id))
    if not db_client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Client Found. ")
    db_job= await db.scalar(select(Job).where(Job.id==new_invoice.job_id, Job.client_id == db_client.id , Job.business_id ==db_business.id))
    if not db_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Job Found. ")
    if new_invoice.discount<0   or new_invoice.discount >= db_job.total_price:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Discount cannot exceed the job total. ")
        
    
    last_number= await db.scalar(select(Invoice.invoice_number).where(Invoice.business_id == db_business.id).order_by(Invoice.invoice_number.desc()))
    if not last_number:
        invoice_number=1
    else:
        invoice_number=last_number+1
    db_invoice=Invoice(
        invoice_number=invoice_number,
        business_id=db_business.id,
        client_id=new_invoice.client_id,
        job_id=new_invoice.job_id,
        total=db_job.total_price,
        discount=new_invoice.discount,
        status=new_invoice.status,
        start_date=new_invoice.start_date,
        due_date=new_invoice.due_date,
        created_at=datetime.now(timezone.utc),
    )
    try: 
        db.add(db_invoice)
        await db.commit()
        return{
            "message":"Invoice was generated. "
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Could not save the invoice")

@router.post("/invoice/quotation/{quotation_id}")
async def invoice__generate_from_quotation(due_date:datetime=Form(),start_date:datetime=Form(),quotation_id:int=Path(gt=0), db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_business= await db.scalar(select(Business).where(Business.user_id ==user_id).with_for_update())
    if not db_business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Business Found. ")
    
    db_quotation= await db.scalar(select(Quotation).join(Business,Quotation.business_id == Business.id).where(Business.user_id ==user_id, Quotation.id == quotation_id))
    if not db_quotation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Quotation Found. ")
    if db_quotation.quotation_status != QuotationStatus.ACCEPTED :
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can not process unaccepted and cancelled Quotation. ")
    existing= await db.scalar(select(Invoice).where(Invoice.quotation_id == db_quotation.id))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"An Invoice already exists for this quotation: Inv id: {existing.id}")
    db_job= await db.scalar(select(Job).where(Job.id == db_quotation.job_id , Job.client_id == db_quotation.client_id, Job.business_id ==db_business.id))
    if not db_job:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Job Dose not match with given quotation id . ")
    last_number= await db.scalar(select(Invoice.invoice_number).where(Invoice.business_id == db_quotation.business_id).order_by(Invoice.invoice_number.desc()))
    if not last_number:
        invoice_number=1
    else:
        invoice_number=last_number+1
    db_invoice=Invoice(
        invoice_number=invoice_number,
        business_id=db_quotation.business_id,
        client_id=db_quotation.client_id,
        job_id=db_quotation.job_id,
        total=db_quotation.total,
        discount=db_quotation.discount,
        status=InvoiceStatus.UNPAID,
        quotation_id=db_quotation.id,

        start_date=start_date,
        due_date=due_date,

        created_at=datetime.now(timezone.utc),
    )
    try: 
        db.add(db_invoice)
        await db.commit()
        return{
            "message":"Invoice was generated. "
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is Down.")

@router.get("/invoice", response_model=list[ShowAllInvoice])
async def invoice__display_all(db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_invoices= await db.scalars(select(Invoice).join(Business, Invoice.business_id == Business.id).where(Business.user_id == user_id))
    db_invoices_list=db_invoices.all()
    return db_invoices_list

@router.get("/invoice/{id}",response_model=ShowInvoice)
async def invoice__display_ById(id:int=Path(gt=0),db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_invoice= await db.scalar(select(Invoice).join(Business, Invoice.business_id == Business.id).where(Business.user_id == user_id, Invoice.id == id))
    if not db_invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Invoice Found. ")
    return db_invoice


@router.delete("/invoice/{id}")
async def invoice__delete(id:int=Path(gt=0),db:AsyncSession=Depends(get_db),payload:dict=Depends(get_current_user_payload)):
    user_id=int(payload.get("sub"))
    db_invoice= await db.scalar(select(Invoice).join(Business, Invoice.business_id == Business.id).where(Business.user_id == user_id, Invoice.id == id))
    if not db_invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Invoice Found. ")
    try:
        db_invoice.status=InvoiceStatus.CANCELLED
        await db.commit()
        return {
            "message": "Invoice was deleted. "
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is Down.")

@router.patch("/invoice/{id}")
async def invoice__update(new_data:UpdateInvoice,id:int=Path(gt=0),payload:dict=Depends(get_current_user_payload),db:AsyncSession=Depends(get_db)):
    user_id=int(payload.get("sub"))
    db_invoice= await db.scalar(select(Invoice).join(Business, Invoice.business_id == Business.id).where(Business.user_id == user_id, Invoice.id == id))
    if not db_invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Invoice Found. ")
    filled_data=new_data.model_dump(exclude_none=True)
    for field , value in filled_data.items():
        setattr(db_invoice,field,value)
    try:
        db_invoice.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return {
            "message":"Values are updated. "
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is Down.")