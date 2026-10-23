from database.database import async_local_session
from jobs import MakeJob , send_verification_email

async def startup(ctx):
    ctx["db"]=async_local_session
    

class WorkerSettings():
    functions=[send_verification_email,MakeJob]
    on_startup=startup
    max_jobs=8
    max_tries=3
    job_timeout=60*5
    poll_delay=10
    queue_read_limit=8