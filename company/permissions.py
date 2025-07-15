from rest_framework.permissions import BasePermission

class HasModulePermission(BasePermission):
    """
    Custom permission class that checks if the employee's job role allows
    access to the requested module and action (view, create, edit, delete).
    """

    def has_permission(self, request, view):
        # Get action type (mapped to request method)
        method_map = {
            'GET': 'view',
            'POST': 'create',
            'PUT': 'edit',
            'PATCH': 'edit',
            'DELETE': 'delete',
        }

        # Ensure user is authenticated and tied to an employee
        if not request.user.is_authenticated or not hasattr(request.user, 'employee'):
            return False

        employee = request.user.employee
        job_role = employee.job_role

        # Determine action
        action_type = method_map.get(request.method)
        if not action_type:
            return False  # Not mapped? Deny by default.

        # Determine module (you might pass this via view)
        module_name = getattr(view, 'module_name', None)
        if not module_name:
            return False

        # Check permission from JobRoleModule table
        return job_role.modules.filter(
            module__name=module_name,
            **{f"can_{action_type}": True}
        ).exists()
