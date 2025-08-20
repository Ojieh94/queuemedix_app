from fastapi import HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app.schemas import RegisterUser
from src.app.models import User, Patient, Hospital, Doctor, Admin
from src.app.core.utils import hash_password
from datetime import date

async def register_user(payload: RegisterUser, session: AsyncSession):
    
    model_dict = payload.model_dump()
    # Create base user
    new_user = User(**model_dict)

    new_user.hashed_password = hash_password(payload.password)

    session.add(new_user)
    await session.flush()  # get new_user.id without committing yet

    # Create profile based on role
    if new_user.role == "patient":
        profile = Patient(
            user_uid=new_user.uid,
            full_name=" ",
            hospital_card_id=" ",
            phone_number=" ",
            date_of_birth=date.today(),
            gender=" ",
            country=" ",
            state_of_residence=" ",
            home_address=" ",
            blood_type=" ",
            emergency_contact_full_name=" ",
            emergency_contact_phone_number=" "
            )
    elif new_user.role == "doctor":
        profile = Doctor(
            user_uid=new_user.uid,
            full_name=" ",
            phone_number=" ",
            date_of_birth=date.today(),
            gender=" ",
            country=" ",
            state_of_residence=" ",
            home_address=" ",
            license_number=" ",
            specialization=" ",
            qualification=" ",
            years_of_experience=0
            )
    elif new_user.role == "hospital":
        profile = Hospital(
            user_uid=new_user.uid,
            hospital_name=" ",
            full_address=" ",
            state="",
            license_number=" ",
            phone_number=" ",
            registration_number=" ",
            hospital_ceo=" "
            )
    elif new_user.role == "admin":
        profile = Admin(
            user_uid=new_user.uid,
            full_name=""
            )
    else:
        raise HTTPException(status_code=400, detail="Invalid role.")

    session.add(profile)
    await session.commit()
    await session.refresh(new_user)

    return new_user
