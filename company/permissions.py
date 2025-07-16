from rest_framework.permissions import BasePermission

from rest_framework.permissions import BasePermission

class HasModulePermission(BasePermission):
    """
    Custom permission class that checks if the employee's job role allows
    access to the requested module and action (view, create, edit, delete).
    """

    def has_permission(self, request, view):
        method_map = {
            'GET': 'view',
            'POST': 'create',
            'PUT': 'edit',
            'PATCH': 'edit',
            'DELETE': 'delete',
        }

        if not request.user.is_authenticated or not hasattr(request.user, 'employee'):
            return False

        employee = request.user.employee
        job_role = employee.job_role
        action_type = method_map.get(request.method)

        if not action_type:
            return False

        module_name = getattr(view, 'module_name', None)
        if not module_name:
            return False

        return job_role.permissions.filter(
            module_name=module_name,
            **{f"can_{action_type}": True}
        ).exists()

