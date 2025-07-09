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
    path('client/create/', CreateClientView.as_view()),
    path('client/list/', ListClientsView.as_view()),
    path('client/<int:pk>/', RetrieveClientView.as_view()),
    path('client/update/<int:pk>/', UpdateClientView.as_view()),
    path('client/delete/<int:pk>/', DeleteClientView.as_view()),

    # Item
    path('item/create/', CreateItemView.as_view()),
    path('item/list/', ListItemsView.as_view()),
    path('item/<int:pk>/', RetrieveItemView.as_view()),
    path('item/update/<int:pk>/', UpdateItemView.as_view()),
    path('item/delete/<int:pk>/', DeleteItemView.as_view()),

    # Invoice
    # Sales Invoice URLs
    path('sales-invoice/create/', CreateSalesInvoiceView.as_view(), name='create_sales_invoice'),
    path('sales-invoice/list/', ListSalesInvoiceView.as_view(), name='list_sales_invoice'),
    path('sales-invoice/delete/<int:pk>/', DeleteSalesInvoiceView.as_view(), name='delete_sales_invoice'),

    # Purchase Invoice URLs
    path('purchase-invoice/create/', CreatePurchaseInvoiceView.as_view(), name='create_purchase_invoice'),
    path('purchase-invoice/list/', ListPurchaseInvoiceView.as_view(), name='list_purchase_invoice'),
    path('purchase-invoice/delete/<int:pk>/', DeletePurchaseInvoiceView.as_view(), name='delete_purchase_invoice'),
]
