from typing import List
from src.app.core import errors
from src.app.models import User, Appointment, UserRoles, AdminType, Department


def access_grant_for_patient_appointments(
    current_user: User, 
    patient, 
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
            return [apt for apt in appointments if apt.hospital_uid == current_user.hospital.uid]

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
            return [apt for apt in appointments if apt.hospital_uid == current_user.hospital.uid]

        else:
            raise errors.NotAuthorized()

    elif current_user.role == UserRoles.HOSPITAL:
        return [apt for apt in appointments if apt.hospital_uid == current_user.hospital.uid]

    elif current_user.role == UserRoles.DOCTOR:
        return [apt for apt in appointments if apt.doctor_uid == current_user.doctor.uid]

    elif current_user.role == UserRoles.PATIENT:
        return {apt for apt in appointments if apt.patient_uid == current_user.patient.uid}
    else:
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
    
    if current_user.role == UserRoles.ADMIN:
        if current_user.admin.admin_type == AdminType.SUPER_ADMIN:
            return
        elif current_user.admin.admin_type in {AdminType.HOSPITAL_ADMIN, AdminType.DEPARTMENT_ADMIN}:
            for dpt in departments:
                if current_user.hospital.uid == dpt.hospital_uid:
                    return
            raise errors.NotAuthorized()
    elif current_user.role == UserRoles.HOSPITAL:
        for dpt in departments:
            if current_user.hospital.uid == dpt.hospital_uid:
                return
        raise errors.NotAuthorized()
    
    elif current_user.role == UserRoles.PATIENT:
        return

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
  
    if current_user.admin.admin_type in {AdminType.DEPARTMENT_ADMIN, AdminType.HOSPITAL_ADMIN}:
        if current_user.hospital.uid == department.hospital_uid:
            return

    raise errors.NotAuthorized()