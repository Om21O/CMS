from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Owner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_no = models.CharField(max_length=15)
    type_of_company = models.CharField(max_length=10, choices=[('basic', 'Basic'), ('premium', 'Premium')])

    def __str__(self):
        return self.user.username

class Company(models.Model):
    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="companies")
    company_name = models.CharField(max_length=255)
    phone_no = models.CharField(max_length=15)
    gst = models.CharField(max_length=15)
    address = models.TextField()
    type_of_company = models.CharField(max_length=50, null=True, blank=True)

class Client(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="clients")
    client_name = models.CharField(max_length=255)
    address = models.TextField()
    gst = models.CharField(max_length=15, null=True, blank=True)
    phone_no = models.CharField(max_length=15)


class Item(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('litre', 'Litre'),
        ('piece', 'Piece'),
        ('meter', 'Meter'),
        ('box', 'Box'),
    ]

    TAX_TYPE_CHOICES = [
        ('withtax', 'With Tax'),
        ('withouttax', 'Without Tax'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)
    item_code = models.CharField(max_length=50, unique=True)
    quantity = models.FloatField()  # numeric value
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    description = models.TextField()
    tax_type = models.CharField(max_length=20, choices=TAX_TYPE_CHOICES)
    tax = models.FloatField(blank=True, null=True)
    price = models.FloatField(help_text="Price per unit (kg, liter, etc.)")
    selling_price = models.FloatField(help_text="Selling price per unit (before or after tax, your choice)", default=0.0, blank=True, null=True)

    def __str__(self):
        return f"{self.item_name} - {self.item_code} ({self.company.company_name})"

    def save(self, *args, **kwargs):
        if self.tax_type == 'withtax' and self.tax is None:
            raise ValueError("Tax must be provided if tax_type is 'withtax'")

        if not self.selling_price or self.selling_price == 0:
            self.selling_price = self.price

        if self.quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        super().save(*args, **kwargs)

        

class Invoice(models.Model):
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='invoices')
    client = models.ForeignKey('Client', on_delete=models.PROTECT, related_name='invoices')
    item = models.ForeignKey('Item', on_delete=models.PROTECT, related_name='invoices')

    invoice_number = models.CharField(max_length=100, unique=True)
    invoice_date = models.DateField(auto_now_add=True)

    quantity = models.PositiveIntegerField()
    rate = models.FloatField()  # Cost price
    line_total = models.FloatField()  # quantity * rate
    price_per_unit = models.FloatField(help_text="Price per unit after tax (final selling price)", default=0, blank=True, null=True)
    total_price = models.FloatField(help_text="Total = price_per_unit * quantity", default=0, blank=True, null=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.client.client_name} - {self.item.item_name}"
    def save(self, *args, **kwargs):
        if self.quantity <= 0:
            raise ValueError("Quantity must be greater than zero")
        if self.rate <= 0:
            raise ValueError("Rate must be greater than zero")
        if self.price_per_unit is None or self.price_per_unit <= 0:
            raise ValueError("Price per unit must be greater than zero")

        self.line_total = round(self.quantity * self.rate, 2)
        self.total_price = round(self.quantity * self.price_per_unit, 2)
        super().save(*args, **kwargs)
    