from rest_framework.permissions import BasePermission

from rest_framework.permissions import BasePermission

from rest_framework.permissions import BasePermission
from .models import EmployeeCompanyMap, ModulePermission

class OwnerOrEmployee(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            print("[DENIED] Not authenticated")
            return False
        if user.is_superuser:
            print("[ALLOWED] Superuser")
            return True
        if hasattr(user, 'owner_profile'):
            print("[ALLOWED] Owner profile")
            return True
        if not hasattr(user, 'employee'):
            print("[DENIED] Not an employee")
            return False

        method_map = {
            'GET': 'view',
            'POST': 'create',
            'PUT': 'edit',
            'PATCH': 'edit',
            'DELETE': 'delete'
        }

        action = method_map.get(request.method)
        if not action:
            return False

        try:
            emp_map = EmployeeCompanyMap.objects.get(employee__user=request.user, is_active=True)
            user_company = emp_map.company   
            user_role = emp_map.job_role
            

            if not user_company or not user_role:
                return False

            permission = ModulePermission.objects.filter(
                job_role=user_role,
                company=user_company,
                module_name=view.module_name
            ).first()

            if not permission:
                return False

            # Special case: POST treated as GET (e.g. for filtering/search APIs)
            if request.method == "POST" and getattr(view, "is_post_as_get", False):
                return permission.can_get_using_post

            # Special case: GET with specific ID (like retrieve view)
            if request.method == "GET" and getattr(view, "is_view_specific", False):
                return permission.can_view_specific

            # Regular permission
            return getattr(permission, f"can_{action}", False)

        except EmployeeCompanyMap.DoesNotExist:
            return False
class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        is_superuser = user.is_superuser
        is_owner = hasattr(user, 'owner_profile') and obj.company in user.owner_profile.companies.all()
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
            return obj.company in user.owner_profile.companies.all()

        # Employee can access their own data
        if hasattr(user, 'employee'):
            return obj.user == user

        return False