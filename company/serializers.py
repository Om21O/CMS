from rest_framework import serializers
from .models import *


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

    class Meta:
        model = SalesInvoice
        fields = '__all__'
class PurchaseInvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseInvoiceItem
        fields = '__all__'

class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    items = PurchaseInvoiceItemSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseInvoice
        fields = '__all__'