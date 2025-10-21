from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.app.database.main import init_db, async_sessionmaker
from src.app.services.sign_up_link import delete_expired_tokens
from src.app.core.errors import register_all_errors
from src.app.middlewares import register_all_middlewares
from src.app.router import (
    auth, 
    patients, 
    admins, 
    appointment, 
    department, 
    doctors, 
    hospital, 
    medical_records, 
    users,
    message)
from src.app.websocket import notification_ws, appointment_ws, support_chat

version = "v1"

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server is starting..................")
    await init_db()
    yield
    print("Server is stopping................")
    print("Server has been stopped.")

app = FastAPI(
    title="Medical Queueing System",
    description="A system designed for hospitals and individual practitioners to eliminate the inefficiencies of uncoordinated patient queues by streamlining and managing appointments effectively.",
    version=version,
    lifespan=lifespan, 
    openapi_url=f"/api/{version}/openapi.json",
    docs_url=f"/api/{version}/docs",
    contact={
        "name": "Queuemedix Team",
        "email": "queuemedix@gmail.com",
        "url": "https://queuemedix.com"
    }
)


#Exception block
register_all_errors(app)
register_all_middlewares(app)


# Async cleanup job
async def cleanup_job():
    async with async_sessionmaker() as session:
        try:
            await delete_expired_tokens(session)
        except Exception as e:
            print(f"Error deleting tokens from database: {e}")


# Start the async scheduler
def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(cleanup_job, trigger="interval", hours=24)
    scheduler.start()
    return scheduler


#app routers
app.include_router(auth.auth_router, prefix=f"/api/{version}")
app.include_router(users.user_router, prefix=f"/api/{version}")
app.include_router(hospital.hp_router, prefix=f"/api/{version}")
app.include_router(department.dept_router, prefix=f"/api/{version}")
app.include_router(patients.pat_router, prefix=f"/api/{version}")
app.include_router(doctors.doctor_router, prefix=f"/api/{version}")
app.include_router(appointment.apt_router, prefix=f"/api/{version}")
app.include_router(admins.admin_router, prefix=f"/api/{version}")
app.include_router(medical_records.med_router, prefix=f"/api/{version}")
app.include_router(message.router, prefix=f"/api/{version}")
app.include_router(message.ws_router, prefix=f"/api/{version}")
app.include_router(notification_ws.router, prefix=f"/api/{version}")
app.include_router(appointment_ws.router, prefix=f"/api/{version}")
app.include_router(support_chat.router, prefix=f"/api/{version}")


@app.get('/')
async def root():
    return{"Medical Queueing System designed by: Queuemedix Team"}