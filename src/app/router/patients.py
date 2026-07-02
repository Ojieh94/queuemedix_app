import uuid

from fastapi import APIRouter, Depends, status
from typing import Optional, List
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.app.database.main import get_session
from src.app.core.dependencies import get_current_user
from src.app.schemas import PatientProfileUpdate, PatientRead, PatientHospitalRead, ReviewRead
from src.app.models import User, UserRoles, Admin, AdminType
from src.app.services import patients as pat_service, hospital as hp_service, review
from src.app.core import errors


pat_router = APIRouter(
    tags=['Patients']
)


@pat_router.patch('/patients/profile-update', status_code=status.HTTP_200_OK, response_model=PatientRead)
async def update_patient_profile(patient_uid: uuid.UUID, payload: PatientProfileUpdate, session: AsyncSession=Depends(get_session), current_user: User = Depends(get_current_user)):

    """
    Update patient route
    """

    patient = await pat_service.get_patient(patient_uid, session)

    if not patient:
        raise errors.PatientNotFound()
    
    #Assign security access
    if patient.user_uid != current_user.uid:
        raise errors.NotAuthorized()
    

    #update patient profile
    updated_patient = await pat_service.update_patient(payload, patient_uid, session)

    return updated_patient


@pat_router.get("/patients", status_code=status.HTTP_200_OK, response_model=List[PatientRead])
async def get_all_patients(skip: int = 0, limit: int = 10, search: Optional[str] = "", session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    """
    Only Admins, Practitioners, Hospitals has access to pull or view all patients
    """
    
    patients = await pat_service.get_all_patients(skip, limit, search, session)

    #authorized roles
    allowed_access = {UserRoles.ADMIN, UserRoles.PRACTITIONER, UserRoles.HOSPITAL}

    #check access
    if current_user.role not in allowed_access:
        raise errors.NotAuthorized()

    return patients

@pat_router.get('/patients/single-patient', status_code=status.HTTP_200_OK, response_model=PatientRead)
async def get_single_patient(patient_uid: uuid.UUID, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    """
    Only Admins, Practitioners, Hospitals or the Patient itself has the access to pull or view patient's info by uid.
    """

    patient = await pat_service.get_patient(patient_uid, session)
    
    if not patient:
        raise errors.PatientNotFound()
    
    #authorized user
    is_hospital = (current_user.hospital is not None and current_user.role in [UserRoles.HOSPITAL, UserRoles.ADMIN])

    is_patient = (current_user.uid == patient.user_uid)

    if not (is_hospital or is_patient):
        raise errors.NotAuthorized()
    
    return patient

@pat_router.get('/patients/patient-card', status_code=status.HTTP_200_OK, response_model=PatientRead)
async def fetch_patient(patient_card_id: str, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):

    """
    Only Admins, Practitioners, Hospitals or the Patient itself has the access to pull or view patient's info by patient hospital card id.
    """

    patient = pat_service.get_patient_by_card(patient_card_id, session)
    
    if not patient:
        raise errors.PatientNotFound()
    
    #authorized roles
    allowed_users = {UserRoles.ADMIN, UserRoles.PRACTITIONER, UserRoles.HOSPITAL}

    #check access
    if current_user.role not in allowed_users:
        raise errors.NotAuthorized()
    
    return patient


@pat_router.delete('/patients/{patient_uid}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(patient_uid: uuid.UUID, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user), admin_user: Admin = Depends(get_current_user)):

    """
    Only Admins[SUPER_ADMIN, HOSPITAL_ADMIN], or the Patient itself has the access to delete.
    """

    #patient availability check
    patient = await pat_service.get_patient(patient_uid, session)
    if not patient:
        raise errors.PatientNotFound()
    
    # authorization block
    allowed_admins = {AdminType.SUPER_ADMIN, AdminType.HOSPITAL_ADMIN}

    # Check if current user is an admin(endpoint is only accessible to super admins and hospital admins)
    if admin_user.admin_type not in allowed_admins and current_user.uid != patient.user_uid:
        raise errors.NotAuthorized()
    
    
    await pat_service.delete_patient(patient_uid, session)


@pat_router.get("/patients/patient_hospitals", status_code=status.HTTP_200_OK, response_model=List[PatientHospitalRead])
async def get_hospital_patients(session: AsyncSession=Depends(get_session), current_user:User = Depends(get_current_user)):
    
    if not current_user.patient:
        raise errors.PatientNotFound()
    
    patient_hospitals = await hp_service.get_patient_hospitals(current_user.patient.uid, session)

    return patient_hospitals


@pat_router.get("/patients/reviews", response_model=list[ReviewRead], tags=["Reviews"])
async def get_patient_reviews(offset: int = 0, limit: int = 20, current_user: User=Depends(get_current_user), session: AsyncSession=Depends(get_session),):

    if not current_user.patient:
        raise errors.NotAuthorized()

    reviews = await review.get_patient_reviews(
        patient_uid=current_user.patient.uid,
        offset=offset,
        limit=limit,
        session=session,
    )

    return reviews