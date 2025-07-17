from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .validators import *
from django.db.models import Sum


class Owner(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING, related_name="owner_profile")
    phone_no = models.CharField(max_length=10, validators=[ValidatePhoneNumber()])
    type_of_company = models.CharField(max_length=10, choices=[('basic', 'Basic'), ('premium', 'Premium')])
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.type_of_company}"


class Company(models.Model):
    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(Owner, max_length=20, on_delete=models.DO_NOTHING, related_name="companies")
    company_name = models.CharField(max_length=55, validators=[ValidateName(field_name="Company name")])
    phone_no = models.CharField(max_length=10, validators=[ValidatePhoneNumber()])
    gst = models.CharField(max_length=15, validators=[validate_gst_format], blank=True, null=True)
    address = models.TextField(validators=[validate_address])
    type_of_company = models.CharField(max_length=50, null=True, blank=True)
    deleted = models.BooleanField(default=False)


class Client(models.Model):
    CLIENT_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('supplier', 'Supplier'),
    ]
    client_type = models.CharField(max_length=10, choices=CLIENT_TYPE_CHOICES, default='customer',null=True, blank=True)
    client_name = models.CharField(max_length=255, validators=[ValidateName(field_name="Client name")])
    mobile_number = models.CharField(max_length=10, validators=[ValidatePhoneNumber()])
    email = models.EmailField(validators=[validate_email_custom])
    gstin = models.CharField(max_length=20, blank=True, null=True, validators=[validate_gst_format])
    pan = models.CharField(max_length=20, blank=True, null=True, validators=[validate_pan])
    state = models.CharField(max_length=50, validators=[ValidateName(field_name="State")])
    billing_address = models.TextField(validators=[validate_address])
    billing_address_line2 = models.CharField(max_length=100, blank=True, null=True, validators=[ValidateIfPresentNotEmpty(field_name="Billing Address Line 2")])
    shipping_address = models.TextField(blank=True, null=True, validators=[ValidateIfPresentNotEmpty(field_name="Shipping Address")])
    pincode_special_economic_zone = models.BooleanField(default=False)
    city = models.CharField(max_length=50, blank=True, null=True, validators=[ValidateIfPresentNotEmpty(field_name="City")])
    credit_period = models.PositiveIntegerField(default=0, help_text="Days")
    credit_limit = models.FloatField(default=0.0, validators=[ValidatePositiveAmount(field_name="Credit Limit")])
    opening_balance = models.FloatField(default=0.0, validators=[ValidatePositiveAmount(field_name="Opening Balance")])
    other_currency = models.BooleanField(default=False)
    check_discount = models.BooleanField(default=False)
    enable_multiple_address = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.client_name} ({self.client_type})"


class Unit(models.Model):
    name = models.CharField(max_length=20, unique=True)
    label = models.CharField(max_length=50)

    def __str__(self):
        return self.label


class TaxType(models.Model):
    code = models.CharField(max_length=20, unique=True)
    label = models.CharField(max_length=50)

    def __str__(self):
        return self.label


class Item(models.Model):
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING)
    item_name = models.CharField(max_length=100, validators=[ValidateName(field_name="Item name")])
    item_code = models.CharField(max_length=50, unique=True)
    quantity = models.FloatField(validators=[ValidatePositiveAmount(field_name="Quantity")])
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    description = models.TextField(validators=[validate_address])
    tax_type = models.ForeignKey(TaxType, on_delete=models.PROTECT, null=True, blank=True)
    tax = models.FloatField(blank=True, null=True, validators=[ValidatePositiveAmount(field_name="Tax")])
    price = models.FloatField(help_text="Base price per unit", validators=[ValidatePositiveAmount(field_name="Price")])
    selling_price = models.FloatField(help_text="Selling price per unit", default=0.0, blank=True, null=True, validators=[ValidatePositiveAmount(field_name="Selling Price")])
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.item_name} - {self.item_code} ({self.company.company_name})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class PaymentStatus(models.Model):
    code = models.CharField(max_length=20, unique=True)
    label = models.CharField(max_length=50)

    def __str__(self):
        return self.label


class PaymentType(models.Model):
    code = models.CharField(max_length=20, unique=True)
    label = models.CharField(max_length=50)

    def __str__(self):
        return self.label


class PaymentMode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    label = models.CharField(max_length=50)

    def __str__(self):
        return self.label


class SalesInvoice(models.Model):
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name='invoices')
    client = models.ForeignKey(Client, on_delete=models.DO_NOTHING, related_name='invoices')
    invoice_number = models.CharField(max_length=100, unique=True, validators=[ValidateInvoiceNumber()])
    invoice_date = models.DateField(auto_now_add=True)
    final_discount_applicable = models.BooleanField(default=False)
    final_discount = models.FloatField(default=0.0, validators=[ValidateDiscount(field_name="Final Discount")])
    total_price = models.FloatField(default=0.0)
    deleted = models.BooleanField(default=False)
    received_amt = models.FloatField(default=0.0, validators=[ValidatePositiveAmount(field_name="Received Amount")])
    payment_status = models.ForeignKey(PaymentStatus, on_delete=models.PROTECT)
    payment_type = models.ForeignKey(PaymentType, on_delete=models.PROTECT)
    payment_mode = models.ForeignKey(PaymentMode, on_delete=models.PROTECT)
    @property
    def pending_amount(self):
        return round(self.total_price - self.paid_amt, 2)
    def calculate_subtotal(self):
        return sum(item.line_total for item in self.items.all())

    def apply_final_discount(self, subtotal):
        if self.final_discount_applicable and self.final_discount > 0:
            return round(subtotal - (subtotal * self.final_discount / 100), 2)
        return round(subtotal, 2)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        subtotal = self.calculate_subtotal()
        self.total_price = self.apply_final_discount(subtotal)
        super().save(update_fields=['total_price'])


class SalesInvoiceItem(models.Model):
    invoice = models.ForeignKey(SalesInvoice, related_name='items', on_delete=models.DO_NOTHING)
    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING)
    quantity = models.PositiveIntegerField(validators=[ValidatePositiveAmount(field_name="Item Quantity")])
    discount_applicable = models.BooleanField(default=False)
    discount = models.FloatField(default=0.0, validators=[ValidateDiscount(field_name="Item Discount")])
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
    supplier_name = models.CharField(max_length=100, validators=[ValidateName(field_name="Supplier Name")])
    invoice_number = models.CharField(max_length=100, unique=True, validators=[ValidateInvoiceNumber()])
    invoice_date = models.DateField(auto_now_add=True)
    total_price = models.FloatField(default=0.0)
    deleted = models.BooleanField(default=False)
    paid_amt = models.FloatField(default=0.0, validators=[ValidatePositiveAmount(field_name="Paid Amount")])
    payment_status = models.ForeignKey(PaymentStatus, on_delete=models.PROTECT)
    payment_type = models.ForeignKey(PaymentType, on_delete=models.PROTECT)
    payment_mode = models.ForeignKey(PaymentMode, on_delete=models.PROTECT)
    @property
    def pending_amount(self):
        return round(self.total_price - self.paid_amt, 2)


class PurchaseInvoiceItem(models.Model):
    invoice = models.ForeignKey(PurchaseInvoice, related_name='items', on_delete=models.DO_NOTHING)
    item_name = models.CharField(max_length=100, validators=[ValidateName(field_name="Purchase Item Name")])
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    quantity = models.FloatField(validators=[ValidatePositiveAmount(field_name="Purchase Quantity")])
    cost_price = models.FloatField(help_text="Unit purchase price (cost)", validators=[ValidatePositiveAmount(field_name="Cost Price")])
    line_total = models.FloatField(blank=True, default=0.0)
    deleted = models.BooleanField(default=False)


class Bank(models.Model):
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name="banks")
    bank_name = models.CharField(max_length=100, validators=[ValidateName(field_name="Bank Name")])
    account_holder_name = models.CharField(max_length=100, validators=[ValidateName(field_name="Account Holder Name")])
    account_no = models.CharField(max_length=30, validators=[validate_account_number])
    ifsc_code = models.CharField(max_length=20, validators=[validate_ifsc_code])
    address = models.TextField(validators=[validate_address])
    branch = models.CharField(max_length=100)
    ad_code = models.CharField(max_length=20, blank=True, null=True)
    swift_code = models.CharField(max_length=20, blank=True, null=True)
    opening_balance = models.FloatField(default=0.0, validators=[ValidatePositiveAmount(field_name="Opening Balance")])
    as_on = models.DateField()

    def __str__(self):
        return f"{self.bank_name} ({self.account_no})"


class BankTransaction(models.Model):
    bank = models.ForeignKey(Bank, on_delete=models.DO_NOTHING, related_name="transactions")
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name="bank_transactions")
    date = models.DateField(auto_now_add=True)
    amount = models.FloatField(validators=[ValidatePositiveAmount(field_name="Transaction Amount")])
    TRANSACTION_TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]
    transaction_type = models.CharField(max_length=6, choices=TRANSACTION_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True, validators=[ValidateIfPresentNotEmpty(field_name="Transaction Description")])

    

class CashLedger(models.Model):
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name="cash_ledgers")
    date = models.DateField(auto_now_add=True)
    amount = models.FloatField(validators=[ValidatePositiveAmount(field_name="Amount")])
    
    TRANSACTION_TYPE_CHOICES = [
        ('inflow', 'Inflow'),
        ('outflow', 'Outflow'),
    ]
    transaction_type = models.CharField(max_length=7, choices=TRANSACTION_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True, validators=[ValidateIfPresentNotEmpty(field_name="Description")])

    def __str__(self):
        return f"{self.date} - {self.transaction_type} - {self.amount}"
    
class JobRole(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
class ModulePermission(models.Model):
    job_role = models.ForeignKey(JobRole, on_delete=models.DO_NOTHING, related_name='permissions')
    module_name = models.CharField(max_length=100)  # E.g., 'Sales Voucher', 'Inventory'
    can_view = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    

    def __str__(self):
        return f"{self.job_role.name} - {self.module_name}"

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, related_name="employees")
    job_role = models.ForeignKey(JobRole, on_delete=models.PROTECT, related_name="employees")
    phone_number = models.CharField(max_length=10, validators=[ValidatePhoneNumber()])
    
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.job_role.name}"
    
