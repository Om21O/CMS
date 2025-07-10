from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
# Create your models here.

class Owner(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING, related_name="owner_profile")
    phone_no = models.CharField(max_length=15)
    type_of_company = models.CharField(max_length=10, choices=[('basic', 'Basic'), ('premium', 'Premium')])
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.type_of_company}"

    

class Company(models.Model):
    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(Owner, on_delete=models.DO_NOTHING, related_name="companies")
    company_name = models.CharField(max_length=255)
    phone_no = models.CharField(max_length=15)
    gst = models.CharField(max_length=15)
    address = models.TextField()
    type_of_company = models.CharField(max_length=50, null=True, blank=True)
    deleted = models.BooleanField(default=False)


class Client(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name="clients")
    client_name = models.CharField(max_length=255)
    address = models.TextField()
    gst = models.CharField(max_length=15, null=True, blank=True)
    phone_no = models.CharField(max_length=15)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.client_name} - {self.company.company_name} ({self.phone_no})"

class Unit(models.Model):
    name = models.CharField(max_length=20, unique=True)  # e.g., 'kg'
    label = models.CharField(max_length=50)              # e.g., 'Kilogram'

    def __str__(self):
        return self.label


class TaxType(models.Model):
    code = models.CharField(max_length=20, unique=True)  # e.g., 'withtax'
    label = models.CharField(max_length=50)              # e.g., 'With Tax'

    def __str__(self):
        return self.label


class Item(models.Model):
   

    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING)
    item_name = models.CharField(max_length=100)
    item_code = models.CharField(max_length=50, unique=True)
    quantity = models.FloatField()
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)         # replaced CharField with FK
    description = models.TextField()
    tax_type = models.ForeignKey(TaxType, on_delete=models.PROTECT,null=True, blank=True)  # replaced CharField with FK
    tax = models.FloatField(blank=True, null=True)
    price = models.FloatField(help_text="Base price per unit")
    selling_price = models.FloatField(help_text="Selling price per unit", default=0.0, blank=True, null=True)
    deleted = models.BooleanField(default=False)
    def __str__(self):

        return f"{self.item_name} - {self.item_code} ({self.company.company_name})"

    def save (self, *args, **kwargs):
        # if self.tax_type =='1':
        #     if self.tax is None:
        #         raise ValueError("Tax must be provided for 'withtax'")
        #     base_price = self.price or 0
        #     base_selling = self.selling_price or 0
        #     self.price = round(base_price * (1 + self.tax / 100), 2)
        #     self.selling_price = round(base_selling * (1 + self.tax / 100), 2)
        # else:
        #     self.price = round(self.price or 0, 2)
            # self.selling_price = round(self.selling_price or 0, 2)

        # if self.quantity <= 0:
        #     raise ValidationError("Quantity must be greater than zero")

        super().save(*args, **kwargs)

        
#sales and pruchase invoice model

class SalesInvoice(models.Model):
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name='invoices')
    client = models.ForeignKey(Client, on_delete=models.DO_NOTHING, related_name='invoices')
    invoice_number = models.CharField(max_length=100, unique=True)
    invoice_date = models.DateField(auto_now_add=True)

    final_discount_applicable = models.BooleanField(default=False)
    final_discount = models.FloatField(default=0.0)  # percentage
    total_price = models.FloatField(default=0.0)
    deleted = models.BooleanField(default=False)

    def calculate_subtotal(self):
        return sum(item.line_total for item in self.items.all())

    def apply_final_discount(self, subtotal):
        if self.final_discount_applicable and self.final_discount > 0:
            return round(subtotal - (subtotal * self.final_discount / 100), 2)
        return round(subtotal, 2)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save first to ensure items can be accessed
        subtotal = self.calculate_subtotal()
        self.total_price = self.apply_final_discount(subtotal)
        super().save(update_fields=['total_price'])  # Save updated price only


class SalesInvoiceItem(models.Model):
    invoice = models.ForeignKey(SalesInvoice, related_name='items', on_delete=models.DO_NOTHING)
    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING)
    quantity = models.PositiveIntegerField()

    discount_applicable = models.BooleanField(default=False)
    discount = models.FloatField(default=0.0)  # percentage
    line_total = models.FloatField(default=0.0)
    deleted = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.item.item_name} - {self.quantity} ({self.invoice.invoice_number})"
    def save(self, *args, **kwargs):
        selling_price = self.item.selling_price or 0
        subtotal = self.quantity * selling_price

        if self.discount_applicable and self.discount > 0:
            subtotal -= subtotal * (self.discount / 100)

        self.line_total = round(subtotal, 2)
        super().save(*args, **kwargs)
class PurchaseInvoice(models.Model):
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name='purchase_invoices')
    supplier_name = models.CharField(max_length=100)
    invoice_number = models.CharField(max_length=100, unique=True)
    invoice_date = models.DateField(auto_now_add=True)
    total_price = models.FloatField(default=0.0)
    deleted = models.BooleanField(default=False)


class PurchaseInvoiceItem(models.Model):
    invoice = models.ForeignKey(PurchaseInvoice, related_name='items', on_delete=models.DO_NOTHING)
    item_name = models.CharField(max_length=100)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    quantity = models.FloatField()
    cost_price = models.FloatField(help_text="Unit purchase price (cost)")
    line_total = models.FloatField(blank=True, default=0.0)
    deleted = models.BooleanField(default=False)
