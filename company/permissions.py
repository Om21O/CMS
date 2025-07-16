from rest_framework.permissions import BasePermission

from rest_framework.permissions import BasePermission

from rest_framework.permissions import BasePermission

class OwnerOrEmployee(BasePermission):
    """
    Allows:
    - Superuser ✅
    - Owner (via owner_profile) ✅
    - Employee with module permission ✅
    """

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
            'DELETE': 'delete',
        }
        action_type = method_map.get(request.method)
        module_name = getattr(view, 'module_name', None)

        print(f"[DEBUG] action_type: {action_type}, module_name: {module_name}")

        if not action_type or not module_name:
            print("[DENIED] Missing action_type or module_name")
            return False

        allowed = user.employee.job_role.permissions.filter(
            module_name=module_name,
            **{f"can_{action_type}": True}
        ).exists()

        print(f"[PERMISSION CHECK] Allowed? {allowed}")
        return allowed

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