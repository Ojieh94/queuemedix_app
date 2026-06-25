from typing import List
import uuid
from src.app.core import errors
from src.app.models import User, Appointment, UserRoles, AdminType, Department


def access_grant_for_patient_appointments(
    current_user: User, 
    patient_uid: uuid.UUID,
    hospital_uid: uuid.UUID
):
    """
    Restrict appointments visibility based on current_user, role & relationship.
    """
    is_hospital_admin = (current_user.admin is not None and current_user.admin.admin_type in [AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN] and current_user.admin.hospital_uid == hospital_uid)
   
    is_hospital = (current_user.hospital is not None and current_user.hospital.uid == hospital_uid)

    is_patient = (current_user.patient is not None and current_user.patient.uid == patient_uid)

    is_practitioner = (current_user.practitioner is not None and current_user.practitioner.hospital_uid == hospital_uid)

    if not (is_patient or is_hospital or is_practitioner or is_hospital_admin):
        raise errors.NotAuthorized()
    return True



def access_grant_for_hospital_appointments(
    current_user: User, 
    appointments: List[Appointment]
) -> List[Appointment]:
    """
    Restrict appointments visibility based on current_user, role & relationship.
    """

    if current_user.admin is not None and current_user.role == UserRoles.ADMIN:
        # Super admin.... unrestricted
        if current_user.admin.admin_type == AdminType.SUPER_ADMIN:
            return appointments

        # Hospital admin.... only appointments in their hospital
        elif current_user.admin.admin_type in {AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN}:
            return [apt for apt in appointments if apt.hospital_uid == current_user.admin.hospital_uid]

        else:
            raise errors.NotAuthorized()

    elif current_user.hospital is not None and current_user.role == UserRoles.HOSPITAL:
        return [apt for apt in appointments if apt.hospital_uid == current_user.hospital.uid]

    elif current_user.practitioner is not None and current_user.role == UserRoles.PRACTITIONER:
        return [apt for apt in appointments if apt.practitioner_uid == current_user.practitioner.uid]

    else:
        raise errors.NotAuthorized()


#general permission without patients
def check_appointment_access(
    current_user: User, 
    appointment: Appointment
) -> Appointment:
    """
    Restrict access to a single appointment based on current_user role.
    Returns the appointment if authorized, otherwise raises error.
    """

    if current_user.admin is not None and current_user.role == UserRoles.ADMIN:
        if current_user.admin.admin_type == AdminType.SUPER_ADMIN:
            return appointment
        
        elif current_user.admin.admin_type in {AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN}:
            if appointment.hospital_uid == current_user.admin.hospital_uid:
                return appointment
            raise errors.NotAuthorized()

    elif current_user.hospital is not None and current_user.role == UserRoles.HOSPITAL:
        if appointment.hospital_uid == current_user.hospital.uid:
            return appointment
        raise errors.NotAuthorized()

    elif current_user.practitioner is not None and current_user.role == UserRoles.PRACTITIONER:
        if appointment.practitioner_uid == current_user.practitioner.uid:
            return appointment
        raise errors.NotAuthorized()

    raise errors.NotAuthorized()


#permission access for appointment reschedule endpoint
def appointment_reschedule_access(
    current_user: User, 
    appointment: Appointment
) -> Appointment:
    """
    Restrict access to a single appointment based on current_user role.
    Returns the appointment if authorized, otherwise raises error.
    """
    if  current_user.patient is not None and current_user.uid == current_user.patient.user_uid:
        return appointment
        raise errors.NotAuthorized()

    elif current_user.admin is not None and current_user.role == UserRoles.ADMIN:
        if current_user.admin.admin_type in {AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN}:
            if appointment.hospital_uid == current_user.admin.hospital_uid:
                return appointment
        raise errors.NotAuthorized()

    elif current_user.hospital is not None and current_user.role == UserRoles.HOSPITAL:
        if appointment.hospital_uid == current_user.hospital.uid:
            return appointment
        raise errors.NotAuthorized()

    elif current_user.practitioner is not None and current_user.role == UserRoles.PRACTITIONER:
        if appointment.practitioner_uid == current_user.practitioner.uid:
            return appointment
        raise errors.NotAuthorized()

   

    raise errors.NotAuthorized()


#general permission with patient
def general_access(
    current_user: User, 
    appointment: Appointment
) -> Appointment:
    """
    Restrict access to a single appointment based on current_user role.
    Returns the appointment if authorized, otherwise raises error.
    """

    if current_user.admin is not None and current_user.role == UserRoles.ADMIN:
        if current_user.admin.admin_type == AdminType.SUPER_ADMIN:
            return appointment
        
        elif current_user.admin.admin_type in {AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN}:
            if appointment.hospital_uid == current_user.admin.hospital_uid:
                return appointment
            raise errors.NotAuthorized()

    elif current_user.role == UserRoles.HOSPITAL:
        if current_user.hospital is not None and appointment.hospital_uid == current_user.hospital.uid:
            return appointment
        raise errors.NotAuthorized()

    elif current_user.role == UserRoles.PRACTITIONER:
        if current_user.practitioner is not None and appointment.practitioner_uid == current_user.practitioner.uid:
            return appointment
        raise errors.NotAuthorized()
    
    elif current_user.role == UserRoles.PATIENT:
        if current_user.patient is not None and appointment.patient_uid == current_user.patient.uid:
            return appointment
        raise errors.NotAuthorized()

    raise errors.NotAuthorized()


#general access
def general_access_list(
    current_user: User,
    appointments: List[Appointment]
) -> List[Appointment]:
    """
    Restrict appointments visibility based on current_user, role & relationship.
    """

    if current_user.admin is not None and current_user.role == UserRoles.ADMIN:
        # Super admin.... unrestricted
        if current_user.admin.admin_type == AdminType.SUPER_ADMIN:
            return appointments

        # Hospital admin.... only appointments in their hospital
        elif current_user.admin.admin_type == AdminType.HOSPITAL_ADMIN:
            if not current_user.admin.hospital:
                raise errors.NotAuthorized()
            return [apt for apt in appointments if apt.hospital_uid == current_user.admin.hospital_uid]

        else:
            raise errors.NotAuthorized()

    elif current_user.role == UserRoles.HOSPITAL:
        if not current_user.hospital:
            raise errors.NotAuthorized()
        return [apt for apt in appointments if apt.hospital_uid == current_user.hospital.uid]

    elif current_user.role == UserRoles.PRACTITIONER:
        if not current_user.practitioner:
            raise errors.NotAuthorized()
        return [apt for apt in appointments if apt.practitioner_uid == current_user.practitioner.uid]

    elif current_user.role == UserRoles.PATIENT:
        if not current_user.patient:
            raise errors.NotAuthorized()
        return [apt for apt in appointments if apt.patient_uid == current_user.patient.uid]

    else:
        raise errors.NotAuthorized()



#assign practitioner permission
def practitioner_assign_access(current_user: User, appointment: Appointment) -> Appointment:
    """
    Restrict access to a single appointment based on current_user role.
    Returns the appointment if authorized, otherwise raises error.
    """
    
    is_hospital_admin = (current_user.admin is not None and current_user.admin.hospital_uid == appointment.hospital_uid)

    is_hospital = (current_user.hospital is not None and current_user.hospital.uid == appointment.hospital_uid)

    is_admin = (current_user.admin is not None and current_user.admin.admin_type == AdminType.SUPER_ADMIN)
        
    if not (is_hospital or is_hospital_admin or is_admin):
        raise errors.NotAuthorized()
    
    return appointment
#
#
#   PERMISSIONS FOR DEPARTMENT ENDPOINTS
#

def check_department_permission(current_user: User, hospital_uid: uuid.UUID):

    # Hospital owner
    if (
        current_user.role == UserRoles.HOSPITAL
        and current_user.hospital
        and current_user.hospital.uid == hospital_uid
    ):
        return

    # Hospital/Department admins
    if (
        current_user.admin is not None
        and current_user.admin.admin_type in {
            AdminType.HOSPITAL_ADMIN,
            AdminType.DEPARTMENT_ADMIN,
        }
        and current_user.admin.hospital_uid == hospital_uid
    ):
        return

    raise errors.NotAuthorized()


def list_department_permission(current_user: User, departments: List[Department]):
    if current_user.role == UserRoles.PATIENT:
        return  # patients can see all

    if current_user.admin is not None and current_user.role == UserRoles.ADMIN:
        if current_user.admin.admin_type == AdminType.SUPER_ADMIN:
            return  # super admins see all
        elif current_user.admin.admin_type == AdminType.HOSPITAL_ADMIN:
            # hospital admin sees only their hospital’s departments
            if all(dpt.hospital_uid == current_user.admin.hospital_uid for dpt in departments):
                return
            raise errors.NotAuthorized()

    if current_user.role == UserRoles.HOSPITAL:
        if current_user.hospital is not None and  all(dpt.hospital_uid == current_user.hospital.uid for dpt in departments):
            return
        raise errors.NotAuthorized()

    raise errors.NotAuthorized()


def get_department_permission(current_user: User, department: Department):
  
    if current_user.admin is not None and current_user.role == UserRoles.ADMIN:
        if current_user.admin.admin_type == AdminType.SUPER_ADMIN:
            return
        elif current_user.admin.admin_type in {AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN}:
            if current_user.admin.hospital_uid == department.hospital_uid:
                return
            raise errors.NotAuthorized()
    elif current_user.role == UserRoles.HOSPITAL:
        if current_user.hospital is not None and current_user.hospital.uid == department.hospital_uid:
            return
        raise errors.NotAuthorized()
    
    elif current_user.role == UserRoles.PATIENT:
        return

    raise errors.NotAuthorized()


def update_department_permission(current_user: User, department: Department):
    # Only Admins or Hospital-level users can access
    if current_user.role not in {UserRoles.ADMIN, UserRoles.HOSPITAL}:
        raise errors.NotAuthorized()

    # If user has an admin account, check admin type
    if current_user.admin:
        if current_user.admin.admin_type in {AdminType.DEPARTMENT_ADMIN, AdminType.HOSPITAL_ADMIN}:
            if current_user.admin.hospital_uid == department.hospital_uid:
                return
        raise errors.NotAuthorized()

    # If user is a hospital-level user (not an admin)
    if current_user.role == UserRoles.HOSPITAL:
        if current_user.hospital and current_user.hospital.uid == department.hospital_uid:
            return

    # Otherwise deny access
    raise errors.NotAuthorized()



# PERMISSIONS FOR MEDICAL RECORDS ENDPOINTS

def can_access_medical_record_role(current_user: User, hospital_uid: uuid.UUID):
    """
    this permission is to enable the hospital and it's admins and maybe the practitioner to update the records
    """

    is_hospital_admin = (current_user.admin is not None and current_user.admin.admin_type in [AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN] and current_user.admin.hospital_uid == hospital_uid)
   
    is_hospital = (current_user.hospital is not None and current_user.hospital.uid == hospital_uid)


    is_practitioner = (current_user.practitioner is not None and current_user.practitioner.hospital_uid == hospital_uid)

    if not (is_hospital or is_practitioner or is_hospital_admin):
        raise errors.NotAuthorized()
    return True

def can_create_medical_record_for_appointment(current_user: User, appointment: Appointment):
    """
    Fine-grained permission check.
    Ensures the user is authorized to create a record for the given appointment.
    """

    # Practitioner can only create record for their own appointment
    if current_user.practitioner is not None and current_user.role == UserRoles.PRACTITIONER:
        if current_user.practitioner.uid != appointment.practitioner_uid:
            raise errors.NotAuthorized()

    # Hospital admin can only create for their hospital
    if (
        current_user.admin is not None and current_user.role == UserRoles.ADMIN
        and current_user.admin.admin_type == AdminType.HOSPITAL_ADMIN
    ):
        if current_user.admin.hospital_uid != appointment.hospital_uid:
            raise errors.NotAuthorized()
        
    if current_user.hospital is not None and current_user.role == UserRoles.HOSPITAL:
        if current_user.hospital.uid != appointment.hospital_uid:
            raise errors.NotAuthorized()

    # Department admin can only create for their department
    if (
        current_user.admin is not None and current_user.role == UserRoles.ADMIN
        and current_user.admin.admin_type == AdminType.DEPARTMENT_ADMIN
    ):
        if current_user.admin.department_uid != appointment.department_uid:
            raise errors.NotAuthorized()

    return True


def get_hospital_medical_record_access(current_user: User, hospital_id: uuid.UUID):
    """
    Basic role check to ensure the user is allowed to access medical records.
    This should run BEFORE fetching any medical record.
    Only Hospital Admins are allowed.
    """

    is_hospital_admin = (current_user.admin is not None and current_user.admin.admin_type in [AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN] and current_user.admin.hospital_uid == hospital_id)
   
    is_hospital = (current_user.hospital is not None and current_user.hospital.uid == hospital_id)

    if not (is_hospital_admin or is_hospital):
        raise errors.NotAuthorized()

    return True


def can_access_medical_records(current_user: User, hospital_uid: uuid.UUID):
    """
    Ensures that only Hospital Admins can access medical records.
    """

    is_hospital_admin = (current_user.admin is not None and current_user.admin.admin_type in [AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN] and current_user.admin.hospital_uid == hospital_uid)

    is_hospital = (current_user.hospital is not None and current_user.hospital.uid == hospital_uid)
    
    if not (is_hospital or is_hospital_admin):
        raise errors.NotAuthorized()

    raise errors.RoleCheckAccess()



def can_access_patient_medical_records(
    current_user: User,
    patient_id: uuid.UUID,
    hospital_id: uuid.UUID,
):
    # print("Current Hospital UID:", current_user.hospital.uid)
    # print("Hospital ID:", hospital_id)
    # print(type(current_user.hospital.uid))
    # print(type(hospital_id))

    is_hospital_admin = (current_user.admin is not None and current_user.admin.admin_type in [AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN] and current_user.admin.hospital_uid == hospital_id)
   
    is_hospital = (current_user.hospital is not None and current_user.hospital.uid == hospital_id)

    is_patient = (current_user.patient is not None and current_user.patient.uid == patient_id)

    is_practitioner = (current_user.practitioner is not None and current_user.practitioner.hospital_uid == hospital_id)

    if not (is_patient or is_hospital or is_practitioner or is_hospital_admin):
        raise errors.NotAuthorized()
    return True

def can_update_medical_record(current_user: User, hospital_uid: uuid.UUID):
    """
    Permission check to ensure the hospitals, its admins, practitioners can update a medical record. Super Admins are not allowed.
    """

    is_hospital_admin = (current_user.admin is not None and current_user.admin.admin_type in [AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN] and current_user.admin.hospital_uid == hospital_uid)
   
    is_hospital = (current_user.hospital is not None and current_user.hospital.uid == hospital_uid)

    is_practitioner = (current_user.practitioner is not None and current_user.practitioner.hospital_uid == hospital_uid)

    if not ( is_hospital or is_practitioner or is_hospital_admin):
        raise errors.NotAuthorized()
    
    return True

def accessible_to_super_admin(current_user: User):
    """
    Ensure the current user is a super admin.
    """

    if current_user.role != UserRoles.ADMIN:
        raise errors.NotAuthorized()

    if current_user.admin is not None and current_user.admin.admin_type != AdminType.SUPER_ADMIN:
        raise errors.NotAuthorized()

    return True