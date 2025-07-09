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
