from rest_framework.permissions import BasePermission

from rest_framework.permissions import BasePermission

from rest_framework.permissions import BasePermission
from .models import EmployeeCompanyMap, ModulePermission,Company

class OwnerOrEmployee(BasePermission):
    """
    Custom permission class that:
    - Allows access to owners of the company.
    - Allows employees only if they have active mapping and proper module permission.
    Uses company_id from URL parameters.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False

        # Get company_id from URL parameters
        company_id = view.kwargs.get('company_id')
        print(f"Permission check - User: {user}, Company ID from URL: {company_id}")

        # Superuser always has access
        if user.is_superuser:
            print("Superuser granted access")
            return True

        module_name = getattr(view, 'module_name', None)
        is_view_specific = getattr(view, 'is_view_specific', False)
        print(f"Module name: {module_name}, View specific: {is_view_specific}")

        # Owner access check
        if hasattr(user, 'owner_profile'):
            print("User is an owner")
            
            # If no company_id in URL, allow access to owner-only views
            if company_id is None:
                print("Owner accessing owner-specific view")
                return True
                
            try:
                # Verify access to specific company
                company_id_int = int(company_id)
                has_access = user.owner_profile.companies.filter(id=company_id_int).exists()
                print(f"Owner access to company {company_id}: {has_access}")
                return has_access
            except (ValueError, TypeError):
                print("Invalid company ID format")
                return False

        # Employee access check
        if hasattr(user, 'employee'):
            print("User is an employee")
            
            if not company_id:
                print("Employee denied: No company ID in URL")
                return False
                
            try:
                company_id_int = int(company_id)
                print(f"Checking employee access for company {company_id}")
                
                emp_map = EmployeeCompanyMap.objects.filter(
                    employee=user.employee,
                    company_id=company_id_int,
                    is_active=True
                ).first()

                if not emp_map:
                    print("Employee has no active mapping to this company")
                    return False

                # No module_name = just company-level access
                if not module_name:
                    print("Employee granted company-level access (no module required)")
                    return True

                print(f"Checking module permissions for: {module_name}")
                # Check if the job role allows access to the specific module
                permission = emp_map.job_role.permissions.filter(
                    module_name=module_name
                ).first()

                if not permission:
                    print(f"No permission found for module: {module_name}")
                    return False

                # If view requires specific object permissions
                if is_view_specific and not permission.can_view_specific:
                    print(f"Employee lacks 'view_specific' permission for {module_name}")
                    return False

                print(f"Employee granted access to module: {module_name}")
                return True

            except (ValueError, TypeError):
                print("Invalid company ID format")
                return False
            except Exception as e:
                print(f"Employee permission error: {str(e)}")
                return False

        print("User has no recognized profile type (not owner, not employee)")
        return False
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