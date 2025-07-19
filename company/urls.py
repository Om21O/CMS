from django.urls import path, include
from .views import *
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [
    # path('swagger/', schema_view.with_ui('swagger', cache_timeout=0)),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # Login and Logout
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Owner
    path('owner/create/', CreateOwnerView.as_view()),
    path('owner/list/', ListOwnersView.as_view()),
    path('owner/<int:pk>/', RetrieveOwnerView.as_view()),
    path('owner/update/<int:pk>/', UpdateOwnerView.as_view()),
    path('owner/delete/<int:pk>/', DeleteOwnerView.as_view()),

    # Company
    path('company/create/', CreateCompanyView.as_view()),
    path('company/list/', ListCompaniesView.as_view()),
    path('company/<int:pk>/', RetrieveCompanyView.as_view()),
    path('company/update/<int:pk>/', UpdateCompanyView.as_view()),
    path('company/delete/<int:pk>/', DeleteCompanyView.as_view()),

    # Client
    path('client/create/<int:company_id>/', CreateClientView.as_view()),
    path('client/list/<int:company_id>/', ListClientsView.as_view()),
    path('client/<int:company_id>/<int:pk>/', RetrieveClientView.as_view()),
    path('client/update/<int:company_id>/<int:pk>/', UpdateClientView.as_view()),
    path('client/delete/<int:company_id>/<int:pk>/', DeleteClientView.as_view()),

    # Item
    path('items/create/<int:company_id>/', CreateItemView.as_view(), name='create-item'),
    path('item/list/<int:company_id>/', ListItemsView.as_view()),
    path('item/<int:company_id>/<int:pk>/', RetrieveItemView.as_view()),
    path('item/update/<int:company_id>/<int:pk>/', UpdateItemView.as_view()),
    path('item/delete/<int:company_id>/<int:pk>/', DeleteItemView.as_view()),

    # Invoice
    # Sales Invoice URLs
    path('sales-invoice/create/<int:company_id>/', CreateSalesInvoiceView.as_view(), name='create_sales_invoice'),
    path('sales-invoice/list/<int:company_id>/', ListSalesInvoiceView.as_view(), name='list_sales_invoice'),
    path('sales-invoice/delete/<int:pk>/<int:company_id>/', SoftDeleteSalesInvoiceView.as_view(), name='delete_sales_invoice'),
    path('sales-invoice/update/<int:company_id>/<int:pk>/', UpdateSalesInvoiceView.as_view(), name='update_sales_invoice'),
    path('sales-invoice/<int:company_id>/<int:pk>/', RetrieveSalesInvoiceView.as_view(), name='retrieve_sales_invoice'),

    # Purchase Invoice URLs
    path('purchase-invoice/create/<int:company_id>/', CreatePurchaseInvoiceView.as_view(), name='create_purchase_invoice'),
    path('purchase-invoice/list/<int:company_id>/', ListPurchaseInvoiceView.as_view(), name='list_purchase_invoice'),
    path('purchase-invoice/delete/<int:company_id>/<int:pk>/', DeletePurchaseInvoiceView.as_view(), name='delete_purchase_invoice'),
    path('purchase-invoice/update/<int:company_id>/<int:pk>/',UpdatePurchaseInvoiceView.as_view(), name='update_purchase_invoice'),
    path('purchase-invoice/<int:company_id>/<int:pk>/', RetrievePurchaseInvoiceView.as_view(), name='retrieve_purchase_invoice'),
    # Paymentin and url
    path('payment-in/create/<int:company_id>/', PaymentInView.as_view(), name='create_payment_in'),
    path('payment-out/create/<int:company_id>/', PaymentOutView.as_view(), name='create_payment_in'),

    path('export-invoice-report/<int:company_id>/', InvoiceReportExportView.as_view()),

    path('jobrole/create/<int:company_id>/', CreateJobRoleWithPermissionsView.as_view()),
    path('jobrole/list/<int:company_id>/', JobRoleListView.as_view()),
    path('jobrole/<int:company_id>/<int:job_role_id>/', JobRoleDetailView.as_view()),
    path('jobrole/update/<int:company_id>/<int:job_role_id>/', JobRoleUpdateView.as_view()),
    path('jobrole/delete/<int:company_id>/<int:job_role_id>/', JobRoleDeleteView.as_view()),

    path('employee/create/', CreateEmployeeView.as_view()),
    path("employee/", EmployeeListView.as_view(), name="employee-list"),
    path('employee/<int:employee_id>/', EmployeeDetailView.as_view()),
    path('employee/update/<int:employee_id>/', EmployeeUpdateView.as_view()),
    path('employee/delete/<int:employee_id>/', EmployeeDeleteView.as_view()),
    
]
