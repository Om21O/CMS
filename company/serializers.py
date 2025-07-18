from rest_framework import serializers
from .models import *
from .constant import *


class OwnerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Owner
        fields = '__all__'
class CompanySerializer(serializers.ModelSerializer):
    bank_balance = serializers.SerializerMethodField()
    cash_in_hand = serializers.SerializerMethodField()
    class Meta:
        model = Company
        fields = '__all__'
    def get_bank_balance(self, obj):
        banks = obj.banks.all()
        total_balance = 0
        for bank in banks:
            opening = bank.opening_balance or 0
            credit = bank.transactions.filter(transaction_type='credit').aggregate(total=Sum('amount'))['total'] or 0
            debit = bank.transactions.filter(transaction_type='debit').aggregate(total=Sum('amount'))['total'] or 0
            total_balance += opening + credit - debit
        return total_balance

    def get_cash_in_hand(self, obj):
        inflow = obj.cash_ledgers.filter(transaction_type='inflow').aggregate(total=Sum('amount'))['total'] or 0
        outflow = obj.cash_ledgers.filter(transaction_type='outflow').aggregate(total=Sum('amount'))['total'] or 0
        return inflow - outflow


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'


class SalesInvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesInvoiceItem
        exclude = ['invoice']  # don't expect invoice in input

class SalesInvoiceSerializer(serializers.ModelSerializer):
    items = SalesInvoiceItemSerializer(many=True, read_only=True)
    pending_amount = serializers.SerializerMethodField()

    class Meta:
        model = SalesInvoice
        fields = '__all__'

    def get_pending_amount(self, obj):
        total = obj.total_price or 0
        received = obj.received_amt or 0
        return round(total - received, 2)
class PurchaseInvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseInvoiceItem
        fields = '__all__'
    

class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    items = PurchaseInvoiceItemSerializer(many=True, read_only=True)
    pending_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = PurchaseInvoice
        fields = '__all__'
    def get_pending_amount(self, obj):
        return round(obj.total_price - obj.paid_amt, 2)

class EmployeeCreateSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    phone_number = serializers.CharField()
    company_id = serializers.IntegerField()
    job_role_id = serializers.IntegerField()

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    

class ModulePermissionInputSerializer(serializers.Serializer):
    module_name = serializers.CharField()
    can_view = serializers.BooleanField()
    can_create = serializers.BooleanField()
    can_edit = serializers.BooleanField()
    can_delete = serializers.BooleanField()

    def validate_module_name(self, value):
        normalized = value.strip().lower()
        internal_name = ALIAS_TO_MODULE_MAP.get(normalized)
        if not internal_name:
            raise serializers.ValidationError(
                f"Invalid module alias: '{value}'. Allowed aliases are: {list(ALIAS_TO_MODULE_MAP.keys())}"
            )
        return internal_name  # return the internal module name

class JobRoleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRole
        fields = '__all__'
class ModulePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModulePermission
        fields = '__all__'
class JobRoleDetailSerializer(serializers.ModelSerializer):
    permissions = ModulePermissionSerializer(many=True, read_only=True)

    class Meta:
        model = JobRole
        fields = ['id', 'name', 'permissions']
        

