from database.models import Job, Services, JobServices
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError 

async def send_verification_email(ctx,otp,email):
    import smtplib
    from email.message import EmailMessage
    msg=EmailMessage()
    msg["From"]=""
    msg["To"]=email
    msg["Subject"]="Account Verification by MS"
    msg.add_alternative(f"<a href=''>Click</a>",subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
        smtp.login("sender","pass")

async def MakeJob(
    ctx,
    business_id,
    client_id,
    title,
    work,
    note,
    end_at,
    job_status,
    created_at,
    start_at,
    service_ids
    ):
    async with ctx["db"]() as db:
        service_ids=set(service_ids)
        if not service_ids:
            raise ValueError("At least one service is required. ")
        db_services = await db.scalars(select(Services).where(Services.id.in_(service_ids), Services.business_id ==business_id))
        db_services_list=db_services.all()
        if len(db_services_list)!= len(service_ids):
            raise ValueError("some services dose not exists. ")
        total=sum(
            service.price
            for service in db_services_list
        )
        new_job=Job(
                business_id=business_id,
                client_id=client_id,
                title=title,
                work=work,
                note=note,
                end_at=end_at,
                job_status=job_status,
                created_at=created_at,
                start_at=start_at,
                total_price=total
            )
        db.add(new_job)
        await db.flush()
            
        try:
            db.add_all([
                JobServices(
                    job_id=new_job.id,
                    service_id=id
                )
                for id in service_ids
            ])
            await db.commit()
        except SQLAlchemyError:
            await db.rollback()
            print("Error occurred")
            raise
        
