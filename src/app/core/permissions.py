from typing import List
from src.app.core import errors
from src.app.models import MedicalRecord, Patient, User, Appointment, UserRoles, AdminType, Department


def access_grant_for_patient_appointments(
    current_user: User, 
    patient: Patient, 
    appointments: List[Appointment]
) -> List[Appointment]:
    """
    Restrict appointments visibility based on current_user, role & relationship.
    """

    if current_user.role == UserRoles.ADMIN:
        # Super admin.... unrestricted
        if current_user.admin.admin_type == AdminType.SUPER_ADMIN:
            return appointments

        # Hospital admin.... only appointments in their hospital
        elif current_user.admin.admin_type == AdminType.HOSPITAL_ADMIN:
            return [apt for apt in appointments if apt.hospital_uid == current_user.admin.hospital_uid]

        else:
            raise errors.NotAuthorized()

    elif current_user.role == UserRoles.HOSPITAL:
        return [apt for apt in appointments if apt.hospital_uid == current_user.hospital.uid]

    elif current_user.role == UserRoles.DOCTOR:
        return [apt for apt in appointments if apt.doctor_uid == current_user.doctor.uid]

    elif current_user.role == UserRoles.PATIENT:
        if current_user.uid != patient.user_uid:
            raise errors.NotAuthorized()
        return appointments

    else:
        raise errors.NotAuthorized()



def access_grant_for_hospital_appointments(
    current_user: User, 
    appointments: List[Appointment]
) -> List[Appointment]:
    """
    Restrict appointments visibility based on current_user, role & relationship.
    """

    if current_user.role == UserRoles.ADMIN:
        # Super admin.... unrestricted
        if current_user.admin.admin_type == AdminType.SUPER_ADMIN:
            return appointments

        # Hospital admin.... only appointments in their hospital
        elif current_user.admin.admin_type in {AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN}:
            return [apt for apt in appointments if apt.hospital_uid == current_user.hospital.uid]

        else:
            raise errors.NotAuthorized()

    elif current_user.role == UserRoles.HOSPITAL:
        return [apt for apt in appointments if apt.hospital_uid == current_user.hospital.uid]

    elif current_user.role == UserRoles.DOCTOR:
        return [apt for apt in appointments if apt.doctor_uid == current_user.doctor.uid]

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

    if current_user.role == UserRoles.ADMIN:
        if current_user.admin.admin_type == AdminType.SUPER_ADMIN:
            return appointment
        
        elif current_user.admin.admin_type in {AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN}:
            if appointment.hospital_uid == current_user.hospital.uid:
                return appointment
            raise errors.NotAuthorized()

    elif current_user.role == UserRoles.HOSPITAL:
        if appointment.hospital_uid == current_user.hospital.uid:
            return appointment
        raise errors.NotAuthorized()

    elif current_user.role == UserRoles.DOCTOR:
        if appointment.doctor_uid == current_user.doctor.uid:
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
    if current_user.role == UserRoles.ADMIN:
        if current_user.admin.admin_type in {AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN}:
            if appointment.hospital_uid == current_user.hospital.uid:
                return appointment
        raise errors.NotAuthorized()

    elif current_user.role == UserRoles.HOSPITAL:
        if appointment.hospital_uid == current_user.hospital.uid:
            return appointment
        raise errors.NotAuthorized()

    elif current_user.role == UserRoles.DOCTOR:
        if appointment.doctor_uid == current_user.doctor.uid:
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

    if current_user.role == UserRoles.ADMIN:
        if current_user.admin.admin_type == AdminType.SUPER_ADMIN:
            return appointment
        
        elif current_user.admin.admin_type in {AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN}:
            if appointment.hospital_uid == current_user.hospital.uid:
                return appointment
            raise errors.NotAuthorized()

    elif current_user.role == UserRoles.HOSPITAL:
        if appointment.hospital_uid == current_user.hospital.uid:
            return appointment
        raise errors.NotAuthorized()

    elif current_user.role == UserRoles.DOCTOR:
        if appointment.doctor_uid == current_user.doctor.uid:
            return appointment
        raise errors.NotAuthorized()
    
    elif current_user.role == UserRoles.PATIENT:
        if appointment.patient_uid == current_user.patient.uid:
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

    if current_user.role == UserRoles.ADMIN:
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

    elif current_user.role == UserRoles.DOCTOR:
        if not current_user.doctor:
            raise errors.NotAuthorized()
        return [apt for apt in appointments if apt.doctor_uid == current_user.doctor.uid]

    elif current_user.role == UserRoles.PATIENT:
        if not current_user.patient:
            raise errors.NotAuthorized()
        return [apt for apt in appointments if apt.patient_uid == current_user.patient.uid]

    else:
        raise errors.NotAuthorized()



#assign doctor permission
def doctor_assign_access(current_user: User, appointment: Appointment) -> Appointment:
    """
    Restrict access to a single appointment based on current_user role.
    Returns the appointment if authorized, otherwise raises error.
    """
    # Only ADMIN or HOSPITAL users can proceed
    if current_user.role not in {UserRoles.ADMIN, UserRoles.HOSPITAL}:
        raise errors.NotAuthorized()

    # ADMIN users
    if current_user.role == UserRoles.ADMIN:
        # Super admins have full access
        if current_user.admin.admin_type == AdminType.SUPER_ADMIN:
            return appointment

        # Hospital and department admins can access only their hospital appointments
        if current_user.admin.admin_type in {AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN}:
            if not current_user.admin.hospital:
                raise errors.NotAuthorized()  # Admin has no hospital assigned
            if appointment.hospital_uid != current_user.admin.hospital.uid:
                raise errors.NotAuthorized()
            return appointment

    # HOSPITAL users
    if current_user.role == UserRoles.HOSPITAL:
        if not current_user.hospital:
            raise errors.NotAuthorized()  # Hospital user has no hospital assigned
        if appointment.hospital_uid != current_user.hospital.uid:
            raise errors.NotAuthorized()
        return appointment

    # Fallback: deny access
    raise errors.NotAuthorized()




#
#
#   PERMISSIONS FOR DEPARTMENT ENDPOINTS
#

def check_department_permission(current_user: User, hospital_uid: str):
    """
    Restrict creation access to Admins of the hospital or Super Admins
    """
    if current_user.role == UserRoles.HOSPITAL:
        if current_user.hospital.uid == hospital_uid:
            return
    
    elif current_user.admin.admin_type in {AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN}:
        if current_user.hospital.uid == hospital_uid:
            return
        raise errors.NotAuthorized()

    raise errors.NotAuthorized()


def list_department_permission(current_user: User, departments: List[Department]):
    if current_user.role == UserRoles.PATIENT:
        return  # patients can see all

    if current_user.role == UserRoles.ADMIN:
        if current_user.admin.admin_type == AdminType.SUPER_ADMIN:
            return  # super admins see all
        elif current_user.admin.admin_type == AdminType.HOSPITAL_ADMIN:
            # hospital admin sees only their hospital’s departments
            if all(dpt.hospital_uid == current_user.hospital.uid for dpt in departments):
                return
            raise errors.NotAuthorized()

    if current_user.role == UserRoles.HOSPITAL:
        if all(dpt.hospital_uid == current_user.hospital.uid for dpt in departments):
            return
        raise errors.NotAuthorized()

    raise errors.NotAuthorized()


def get_department_permission(current_user: User, department: Department):
  
    if current_user.role == UserRoles.ADMIN:
        if current_user.admin.admin_type == AdminType.SUPER_ADMIN:
            return
        elif current_user.admin.admin_type in {AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN}:
            if current_user.hospital.uid == department.hospital_uid:
                return
            raise errors.NotAuthorized()
    elif current_user.role == UserRoles.HOSPITAL:
        if current_user.hospital.uid == department.hospital_uid:
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
            if current_user.hospital and current_user.hospital.uid == department.hospital_uid:
                return
        raise errors.NotAuthorized()

    # If user is a hospital-level user (not an admin)
    if current_user.role == UserRoles.HOSPITAL:
        if current_user.hospital and current_user.hospital.uid == department.hospital_uid:
            return

    # Otherwise deny access
    raise errors.NotAuthorized()



# PERMISSIONS FOR MEDICAL RECORDS ENDPOINTS

def can_access_medical_record_role(current_user: User):
    """
    Basic role check to ensure the user is allowed to create medical records.
    This should run BEFORE fetching any appointment.
    """

    if current_user.role not in [UserRoles.DOCTOR, UserRoles.ADMIN]:
        raise errors.NotAuthorized()

    if (
        current_user.role == UserRoles.ADMIN
        and current_user.admin.admin_type not in [AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN]
    ):
        raise errors.NotAuthorized()

    return True


def can_create_medical_record_for_appointment(current_user: User, appointment: Appointment):
    """
    Fine-grained permission check.
    Ensures the user is authorized to create a record for the given appointment.
    """

    # Doctor can only create record for their own appointment
    if current_user.role == UserRoles.DOCTOR:
        if current_user.doctor.uid != appointment.doctor_uid:
            raise errors.NotAuthorized()

    # Hospital admin can only create for their hospital
    if (
        current_user.role == UserRoles.ADMIN
        and current_user.admin.admin_type == AdminType.HOSPITAL_ADMIN
    ):
        if current_user.admin.hospital_uid != appointment.hospital_uid:
            raise errors.NotAuthorized()

    # Department admin can only create for their department
    if (
        current_user.role == UserRoles.ADMIN
        and current_user.admin.admin_type == AdminType.DEPARTMENT_ADMIN
    ):
        if current_user.admin.department_uid != appointment.department_uid:
            raise errors.NotAuthorized()

    return True


def get_hospital_medical_record_access(current_user: User, hospital_id: str):
    """
    Basic role check to ensure the user is allowed to access medical records.
    This should run BEFORE fetching any medical record.
    Only Hospital Admins are allowed.
    """

    if current_user.role != UserRoles.ADMIN and current_user.admin.admin_type != AdminType.HOSPITAL_ADMIN:
        raise errors.NotAuthorized()

    if current_user.admin.hospital_uid != hospital_id:
        raise errors.NotAuthorized()

    return True


def can_access_medical_records(current_user: User):
    """
    Ensures that only Hospital Admins can access medical records.
    """
    if current_user.role == UserRoles.ADMIN:
        if current_user.admin.admin_type == AdminType.HOSPITAL_ADMIN:
            return True
        raise errors.NotAuthorized()

    raise errors.RoleCheckAccess()



def can_access_patient_medical_records(current_user: User, patient_id: str, hospital_id: str):
    """
    Permission check to ensure the user can access a patient's medical records.
    """
    if current_user.role == UserRoles.ADMIN:
        if current_user.admin.admin_type == AdminType.SUPER_ADMIN:
            raise errors.RoleCheckAccess()
        if current_user.admin.hospital_uid != hospital_id:
            raise errors.NotAuthorized()

    if current_user.role == UserRoles.PATIENT:
        if current_user.patient.uid != patient_id:
            raise errors.NotAuthorized()

    if current_user.role == UserRoles.DOCTOR:
        if current_user.doctor.hospital_uid != hospital_id:
            raise errors.NotAuthorized()

    return True

def can_update_medical_record(current_user: User, medical_record: MedicalRecord):
    """
    Permission check to ensure the user can update a medical record. Super Admins are not allowed.
    """

    if current_user.role == UserRoles.ADMIN:
        if current_user.admin.admin_type == AdminType.SUPER_ADMIN:
            raise errors.RoleCheckAccess()
        if current_user.admin.hospital_uid != medical_record.hospital_uid:
            raise errors.NotAuthorized()
        
    if current_user.role == UserRoles.DOCTOR:
        if current_user.doctor.uid != medical_record.doctor_uid:
            raise errors.NotAuthorized()
    
    return True

def accessible_to_super_admin(current_user: User):
    """
    Ensure the current user is a super admin.
    """

    if current_user.role != UserRoles.ADMIN:
        raise errors.NotAuthorized()

    if current_user.admin.admin_type != AdminType.SUPER_ADMIN:
        raise errors.NotAuthorized()

    return True