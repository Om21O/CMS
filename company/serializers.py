from rest_framework import serializers
from .models import *


class OwnerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Owner
        fields = ['id', 'username', 'email', 'phone_no', 'type_of_company']
class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'owner', 'company_name', 'phone_no', 'gst', 'address', 'type_of_company']


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'company', 'client_name', 'address', 'gst', 'phone_no']

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'company', 'item_name', 'item_code', 'quantity', 'unit', 'description', 'tax_type', 'tax', 'price', 'selling_price']

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['id', 'company', 'client', 'item', 'invoice_number', 'invoice_date', 'quantity', 'rate', 'line_total', 'price_per_unit', 'total_price']
        read_only_fields = ['id']