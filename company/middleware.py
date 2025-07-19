# from company.models import Company
# from django.utils.deprecation import MiddlewareMixin

# class CompanyMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         user = request.user
#         request.company_id = None  # Initialize as None

#         if user.is_authenticated:
#             try:
#                 # 1. First check if user is an owner
#                 if hasattr(user, 'owner_profile'):
#                     owner = user.owner_profile
#                     # Get the first active company for owners
#                     company = owner.companies.filter(deleted=False).first()
#                     if company:
#                         request.company_id = company.id
#                         print(f"Middleware set owner company: {company.id}")
                
#                 # 2. Then check if user is an employee
#                 elif hasattr(user, 'employee'):
#                     employee = user.employee
#                     active_map = employee.company_links.filter(is_active=True).first()
#                     if active_map:
#                         request.company_id = active_map.company.id
#                         print(f"Middleware set employee company: {active_map.company.id}")
                
#                 # 3. Log if no company found
#                 if not request.company_id:
#                     print(f"No active company found for user: {user.username}")
                    
#             except Exception as e:
#                 print(f"CompanyMiddleware error: {str(e)}")

#         response = self.get_response(request)
#         return response