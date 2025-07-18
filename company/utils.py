from company.models import EmployeeCompanyMap

def get_user_company_from_map(user):
    """
    Returns the active company linked to the employee for the given user.
    Uses select_related to avoid additional DB hits.
    """
    try:
        emp_map = EmployeeCompanyMap.objects.select_related("company", "employee__user").get(
            employee__user=user,
            is_active=True
        )
        return emp_map.company
    except EmployeeCompanyMap.DoesNotExist:
        return None