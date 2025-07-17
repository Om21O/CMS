from django.contrib import admin
from .models import * 
# Register your models here.

admin.site.register(Owner)
admin.site.register(Company)
admin.site.register(Client)
admin.site.register(Item)
admin.site.register(Unit)
admin.site.register(TaxType)
admin.site.register(SalesInvoice)
admin.site.register(SalesInvoiceItem)
admin.site.register(PurchaseInvoice)
admin.site.register(PurchaseInvoiceItem)
admin.site.register(PaymentStatus)
admin.site.register(PaymentType)
admin.site.register(PaymentMode)
admin.site.register(Bank)
admin.site.register(BankTransaction)
admin.site.register(JobRole)
admin.site.register(Employee)
admin.site.register(ModulePermission)
admin.site.register(EmployeeCompanyMap)