from rest_framework.permissions import BasePermission

from rest_framework.permissions import BasePermission

from rest_framework.permissions import BasePermission
from .models import EmployeeCompanyMap, ModulePermission

class OwnerOrEmployee(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        # Get company_id from request (you may modify this to suit your URL kwarg or query param logic)
        company_id = request.parser_context['kwargs'].get('company_id') or request.query_params.get('company_id')
        if not company_id:
            return False

        # Owner logic
        if hasattr(user, 'owner_profile'):
            # Allow if the company belongs to the owner
            if user.owner_profile.companies.filter(id=company_id).exists():
                return True
            return False

        # Employee logic
        if not hasattr(user, 'employee'):
            return False

        try:
            emp_map = EmployeeCompanyMap.objects.get(
                employee__user=user,
                company__id=company_id,
                is_active=True
            )
        except EmployeeCompanyMap.DoesNotExist:
            return False

        job_role = emp_map.job_role
        if not job_role:
            return False

        method_to_action = {
            'GET': 'view',
            'POST': 'create',
            'PUT': 'edit',
            'PATCH': 'edit',
            'DELETE': 'delete',
        }

        action = method_to_action.get(request.method)
        if not action:
            return False

        permission = ModulePermission.objects.filter(
            job_role=job_role,
            company__id=company_id,
            module_name=view.module_name
        ).first()

        if not permission:
            return False

        if request.method == "POST" and getattr(view, "is_post_as_get", False):
            return permission.can_get_using_post

        if request.method == "GET" and getattr(view, "is_view_specific", False):
            return permission.can_view_specific

        return getattr(permission, f"can_{action}", False)

class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        is_superuser = user.is_superuser

        # Get the employee's company from EmployeeCompanyMap
        try:
            emp_company = EmployeeCompanyMap.objects.get(employee=obj, is_active=True).company
        except EmployeeCompanyMap.DoesNotExist:
            return False  # If mapping not found, deny permission

        # Check if user is owner of that company
        is_owner = hasattr(user, 'owner_profile') and emp_company in user.owner_profile.companies.all()
        return is_owner or is_superuser



class IsSelfOrOwner(BasePermission):
    """
    Allows access if:
    - The user is the employee being viewed (self)
    - The user is a superuser
    - The user is an owner and the employee belongs to one of their companies
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Superuser has full access
        if user.is_superuser:
            return True

        # Owner: check if employee is part of their companies
        if hasattr(user, 'owner_profile'):
            try:
                emp_company = EmployeeCompanyMap.objects.get(employee=obj, is_active=True).company
                return emp_company in user.owner_profile.companies.all()
            except EmployeeCompanyMap.DoesNotExist:
                return False

        # Employee can access their own data
        if hasattr(user, 'employee'):
            return obj.user == user

        return False