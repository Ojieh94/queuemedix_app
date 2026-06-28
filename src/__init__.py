from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.app.database.main import init_db, async_session_factory
from src.app.services.invitation import delete_expired_tokens
from src.app.services import appointment as appt_service
from src.app.core.errors import register_all_errors
from src.app.middlewares import register_all_middlewares
from src.app.router import (
    auth, 
    patients, 
    admins, 
    appointment, 
    department, 
    hospital, 
    medical_records,
    practitioners, 
    users,
    message,
    statistics, queue, hospital_media)
from src.app.websocket import notification_ws, appointment_ws, support_chat

version = "v1"

async def mark_missed_appointments_job():
    print("Running missed appointments job...")

    async with async_session_factory() as session:
        updated = await appt_service.mark_missed_appointments(
            session=session
        )

        print(f"{updated} appointments marked as missed")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server is starting..................")
    scheduler = start_scheduler()
    await init_db()
    yield
    print("Server is stopping................")
    print("Scheduler stopping...........")
    scheduler.shutdown()
    print("Scheduler has been stopped")
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
    async with async_session_factory() as session:
        try:
            await delete_expired_tokens(session)
        except Exception as e:
            print(f"Error deleting tokens from database: {e}")


# Start the async scheduler
def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(cleanup_job, trigger="interval", hours=24)
    scheduler.add_job(
        mark_missed_appointments_job,
        trigger="interval",
        minutes=30,
    )
    scheduler.start()
    return scheduler


#app routers
app.include_router(auth.auth_router, prefix=f"/api/{version}")
app.include_router(users.user_router, prefix=f"/api/{version}")
app.include_router(hospital.hp_router, prefix=f"/api/{version}")
app.include_router(hospital_media.media_router, prefix=f"/api/{version}")
app.include_router(statistics.stats_router, prefix=f"/api/{version}")
app.include_router(department.dept_router, prefix=f"/api/{version}")
app.include_router(patients.pat_router, prefix=f"/api/{version}")
app.include_router(practitioners.practitioner_router, prefix=f"/api/{version}")
app.include_router(appointment.apt_router, prefix=f"/api/{version}")
app.include_router(admins.admin_router, prefix=f"/api/{version}")
app.include_router(queue.queue_router, prefix=f"/api/{version}")
app.include_router(medical_records.med_router, prefix=f"/api/{version}")
app.include_router(message.router, prefix=f"/api/{version}")
app.include_router(message.ws_router, prefix=f"/api/{version}")
app.include_router(notification_ws.router, prefix=f"/api/{version}")
app.include_router(appointment_ws.router, prefix=f"/api/{version}")
app.include_router(support_chat.router, prefix=f"/api/{version}")


@app.get('/')
async def root():
    return{"Medical Queueing System designed by: Queuemedix Team"}