from fastapi import HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.app.schemas import RegisterUser, RegisterAdminUser
from src.app.models import User, Patient, Hospital, Doctor, Admin, AdminType, SignupLink, Queue
from src.app.core.utils import hash_password
from datetime import date, datetime, timedelta, timezone
import uuid

def generate_username(role: str) -> str:
    unique_part = uuid.uuid4().hex[:6].upper()

    return f"{role[:3].upper()}-{unique_part}"


async def register_user(payload: RegisterUser, session: AsyncSession):

    model_dict = payload.model_dump()
    # Create base user
    new_user = User(**model_dict, username=generate_username(payload.role.value))

    new_user.hashed_password = hash_password(payload.password)

    session.add(new_user)
    await session.flush()  # get new_user.id without committing yet

    # Create profile based on role
    if new_user.role == "patient":
        profile = Patient(
            user_uid=new_user.uid,
            first_name=" ",
            middle_name="",
            last_name="",
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
            first_name=" ",
            middle_name="",
            last_name="",
            phone_number=" ",
            date_of_birth=date.today(),
            gender=" ",
            country=" ",
            state_of_residence=" ",
            home_address=" ",
            license_number=f"PendingDoctorLicense-{new_user.uid}",
            specialization=" ",
            qualification=" ",
            years_of_experience=0
        )
    elif new_user.role == "hospital":
        profile = Hospital(
            user_uid=new_user.uid,
            hospital_name=f"Pending-{new_user.uid}",
            full_address=" ",
            state="",
            license_number=f"PendingLicense-{new_user.uid}",
            phone_number=" ",
            registration_number=f"PendingReg-{new_user.uid}",
            hospital_ceo=" ",
            cover_image=""
        )

    else:
        raise HTTPException(status_code=400, detail="Invalid role.")

    session.add(profile)

    if new_user.role == "hospital":
        await session.flush()

        print(f"Hospital UUID: {profile.uid}")
        print(f"Hospital Name: {profile.hospital_name}")

        queue = Queue(
            hospital_uid=profile.uid,
            name="Main Queue",
        )

        session.add(queue)
        print("Queue created:", queue)

    await session.commit()
    print("Committed successfully")
    await session.refresh(new_user)

    return new_user


async def register_user_test(payload: RegisterUser, session: AsyncSession):
    """
    Test registration endpoint - automatically verifies user without email requirement.
    For deployment testing only.
    """
    model_dict = payload.model_dump()
    # Create base user
    new_user = User(**model_dict, username=generate_username(payload.role.value))

    new_user.hashed_password = hash_password(payload.password)
    new_user.is_active = True  # Auto-verify the user

    session.add(new_user)
    await session.flush()  # get new_user.id without committing yet

    # Create profile based on role
    if new_user.role == "patient":
        profile = Patient(
            user_uid=new_user.uid,
            first_name=" ",
            middle_name="",
            last_name="",
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
            first_name=" ",
            middle_name="",
            last_name="",
            phone_number=" ",
            date_of_birth=date.today(),
            gender=" ",
            country=" ",
            state_of_residence=" ",
            home_address=" ",
            license_number=f"PendingDoctorLicense-{new_user.uid}",
            specialization=" ",
            qualification=" ",
            years_of_experience=0
        )
    elif new_user.role == "hospital":
        profile = Hospital(
            user_uid=new_user.uid,
            hospital_name=f"Pending-{new_user.uid}",
            full_address=" ",
            state="",
            license_number=f"PendingLicense-{new_user.uid}",
            phone_number=" ",
            registration_number=f"PendingReg-{new_user.uid}",
            hospital_ceo=" ",
            cover_image=""
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid role.")

    session.add(profile)


    if new_user.role == "hospital":
        await session.flush()

        print(f"Hospital UUID: {profile.uid}")
        print(f"Hospital Name: {profile.hospital_name}")

        queue = Queue(
            hospital_uid=profile.uid,
            name="Main Queue",
        )

        session.add(queue)
        print("Queue created:", queue)

    await session.commit()
    print("Committed successfully")
    await session.refresh(new_user)

    return new_user


async def register_admin(payload: RegisterAdminUser, token: str, session: AsyncSession):

    # Validate the signup token
    signup_link = (await session.execute(select(SignupLink).where(SignupLink.token == token))).scalar_one_or_none()
    if not signup_link:
        raise HTTPException(status_code=400, detail="Invalid signup token")

    if signup_link.is_used:
        raise HTTPException(
            status_code=400, detail="Signup token already used")

    # Check if token is expired (optional)
    if signup_link.created_at < datetime.now(timezone.utc) - timedelta(hours=24):
        raise HTTPException(status_code=400, detail="Signup token has expired")

    # Check if the email associated with the token matches the payload
    if signup_link.email != payload.email:
        raise HTTPException(
            status_code=400, detail="Token email does not match")

    # Mark the token as used
    signup_link.is_used = True

    model_dict = payload.model_dump()

    # Create base user
    new_user = User(**model_dict, username=generate_username(payload.role.value))

    new_user.hashed_password = hash_password(payload.password)
    new_user.is_active = True

    session.add(new_user)
    await session.flush()  # get new_user.id without committing yet

    # Create profile based on role
    profile = Admin(
        user_uid=new_user.uid,
        first_name=" ",
        middle_name="",
        last_name="",
        admin_type=signup_link.admin_type,
        hospital_uid=signup_link.hospital_uid,
        notes=signup_link.notes,
        department_uid=signup_link.department_uid
    )

    session.add(profile)
    await session.commit()
    await session.refresh(new_user)

    return new_user


async def register_super_admin(payload: RegisterAdminUser, session: AsyncSession):

    model_dict = payload.model_dump()

    # Create base user
    new_user = User(**model_dict, username=generate_username(payload.role.value))

    new_user.hashed_password = hash_password(payload.password)

    session.add(new_user)
    await session.flush()  # get new_user.id without committing yet

    # Create profile based on role
    profile = Admin(
        user_uid=new_user.uid,
        first_name=" ",
        middle_name="",
        last_name="",
        admin_type=AdminType.SUPER_ADMIN
    )

    session.add(profile)
    await session.commit()
    await session.refresh(new_user)

    return new_user
