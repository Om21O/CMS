from django.shortcuts import render
from django.http import HttpResponse
from .models import *
from django.utils import timezone
from .serializers import *
from rest_framework import viewsets
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework import permissions
from django.db import transaction
from rest_framework.exceptions import ValidationError
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi
# Create your views here.


# schema_view = get_schema_view(
#     openapi.Info(title="My API", default_version='v1'),
#     public=True,
#     permission_classes=[AllowAny],  # Optional
# )
# from drf_yasg.utils import swagger_auto_schema

class LoginView(APIView):
    permission_classes = [AllowAny]  # Allow any user to access this view
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Username and password are required", "status": 400})

        user = authenticate( username=username, password=password)

        if user is not None:
            user_role = "owner" if hasattr(user, 'owner') else "user"

            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "username": user.username,
                "user_role": user_role,
                "status": 200
            })
        else:
            return Response({"error": "Invalid credentials", "status": 400})


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        
        refresh_token = request.data["refresh"]
        if not refresh_token:
             return Response({"error": "Refresh token is required", "status": 400})
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"msg": "Logout successful", "status": 200})
        
        except Exception as e:
            return Response({"error": str(e), "status": 400})




class CreateOwnerView(APIView):
    # You can make it public or protected — up to you
    #permission_classes = [AllowAny]
    # @swagger_auto_schema(request_body=ClientSerializer)
    permission_classes = [AllowAny]
    def post(self, request):
        data = request.data
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        phone_no = data.get('phone_no')
        type_of_company = data.get('type_of_company')  # 'basic' or 'premium'

        if not all([username, email, password, phone_no, type_of_company]):
            return Response({"error": "All fields are required."}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=400)

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already exists"}, status=400)

        if type_of_company not in ['basic', 'premium']:
            return Response({"error": "type_of_company must be 'basic' or 'premium'"}, status=400)

        try:
            with transaction.atomic(): # will roleback if any error occurs
                # Create the user and owner in a single transaction
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )

                owner = Owner.objects.create(
                    user=user,
                    phone_no=phone_no,
                    type_of_company=type_of_company
                )


            return Response({
                "message": "Owner created successfully",
                "user_id": user.id,
                "owner_id": owner.id
                , "status": 201
            })

        except Exception as e:
            return Response({"error": str(e), "status": 500})

class OwnerDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            owner = Owner.objects.get(pk=pk)
        except Owner.DoesNotExist:
            return Response({"error": "Owner not found" , "status": 404})

        serializer = OwnerSerializer(owner)
        return Response({"info":serializer.data, "status":200})
    

# ------------------ COMPANY CREATE ------------------
class CreateCompanyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        owner_id = data.get('owner_id')
        company_name = data.get('company_name')
        phone_no = data.get('phone_no')
        gst = data.get('gst')
        address = data.get('address')
        type_of_company = data.get('type_of_company')

        # Bank details from request
        bank_name = data.get('bank_name')
        account_holder_name = data.get('account_holder_name')
        account_no = data.get('account_no')
        ifsc_code = data.get('ifsc_code')
        bank_address = data.get('bank_address')
        branch = data.get('branch')
        ad_code = data.get('ad_code')
        swift_code = data.get('swift_code')
        opening_balance = data.get('opening_balance', 0.0)
        as_on = data.get('as_on')

        # Validate company fields
        if not all([owner_id, company_name, phone_no, gst, address]):
            return Response({"error": "Missing required company fields", "status": 400}, status=400)
        # Validate bank fields
        if not all([bank_name, account_holder_name, account_no, ifsc_code, bank_address, branch, opening_balance, as_on]):
            return Response({"error": "Missing required bank fields", "status": 400}, status=400)

        try:
            owner = Owner.objects.get(id=owner_id)
        except Owner.DoesNotExist:
            return Response({"error": "Owner not found", "status": 404}, status=404)

        limit = 3 if owner.type_of_company == 'basic' else 5
        current = Company.objects.filter(owner=owner).count()

        if current >= limit:
            return Response({
                "error": f"{owner.type_of_company} plan allows only {limit} companies",
                "status": 400
            }, status=400)

        try:
            with transaction.atomic():
                company = Company.objects.create(
                    owner=owner,
                    company_name=company_name,
                    phone_no=phone_no,
                    gst=gst,
                    address=address,
                    type_of_company=type_of_company
                )

                Bank.objects.create(
                    company=company,
                    bank_name=bank_name,
                    account_holder_name=account_holder_name,
                    account_no=account_no,
                    ifsc_code=ifsc_code,
                    address=bank_address,
                    branch=branch,
                    ad_code=ad_code,
                    swift_code=swift_code,
                    opening_balance=opening_balance,
                    as_on=as_on
                )

            return Response({
                "msg": "Company and Bank created successfully",
                "company_id": company.id
            }, status=201)

        except Exception as e:
            return Response({"error": str(e), "status": 500})

# ------------------ CLIENT CREATE ------------------
class CreateClientView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data

        required_fields = ['client_type', 'client_name', 'mobile_number', 'email', 'gstin', 'state', 'billing_address']
        if not all(data.get(field) for field in required_fields):
            return Response({"error": "Missing required fields", "status": 400}, status=400)

        try:
            client = Client.objects.create(
                client_type=data.get('client_type'),
                client_name=data.get('client_name'),
                mobile_number=data.get('mobile_number'),
                email=data.get('email'),
                gstin=data.get('gstin'),
                pan=data.get('pan'),
                state=data.get('state'),
                billing_address=data.get('billing_address'),
                billing_address_line2=data.get('billing_address_line2'),
                shipping_address=data.get('shipping_address'),
                pincode_special_economic_zone=data.get('pincode_special_economic_zone', False),
                city=data.get('city'),
                credit_period=data.get('credit_period', 0),
                credit_limit=data.get('credit_limit', 0.0),
                opening_balance=data.get('opening_balance', 0.0),
                other_currency=data.get('other_currency', False),
                check_discount=data.get('check_discount', False),
                enable_multiple_address=data.get('enable_multiple_address', False)
            )
            return Response({
                "msg": "Client created successfully",
                "client_id": client.id
            }, status=201)

        except Exception as e:
            return Response({"error": str(e), "status": 500}, status=500)

           

# ------------------ ITEM CREATE ------------------
class CreateItemView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        company_id = data.get('company_id')
        item_name = data.get('item_name')
        item_code = data.get('item_code')
        unit_id = data.get('unit')
        quantity_raw = data.get('quantity')
        description = data.get('description')
        tax_type_id = data.get('tax_type')
        tax = data.get('tax')
        price = data.get('price')
        selling_price = data.get('selling_price', price)

        # --- Validate required fields ---
        if not all([company_id, item_name, item_code, unit_id, description, tax_type_id, price]):
            return Response({"error": "Missing required fields", "status": 400}, status=400)

        # --- Validate numeric fields ---
        try:
            quantity = float(quantity_raw)
            if quantity <= 0:
                return Response({"error": f"Quantity must be > 0. Got {quantity}"}, status=400)
        except (ValueError, TypeError):
            return Response({"error": "Quantity must be a valid number"}, status=400)

        try:
            price = float(price)
        except (ValueError, TypeError):
            return Response({"error": "Price must be a valid number"}, status=400)

        try:
            selling_price = float(selling_price or price)
        except (ValueError, TypeError):
            return Response({"error": "Selling price must be a valid number"}, status=400)

        # --- Get related objects ---
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response({"error": "Company not found", "status": 404}, status=404)

        if Item.objects.filter(item_code=item_code).exists():
            return Response({"error": "Item code must be unique", "status": 400}, status=400)

        try:
            unit = Unit.objects.get(id=unit_id)
        except Unit.DoesNotExist:
            return Response({"error": "Unit not found", "status": 404}, status=404)

        try:
            tax_type = TaxType.objects.get(id=tax_type_id)
        except TaxType.DoesNotExist:
            return Response({"error": "TaxType not found", "status": 404}, status=404)

        # --- Tax and price calculation ---
        if tax_type.code == '1':  # assuming '1' is the code for "with tax"
            if tax is None:
                return Response({"error": "Tax is required for 'withtax' items", "status": 400}, status=400)
            try:
                tax = float(tax)
            except ValueError:
                return Response({"error": "Invalid tax value", "status": 400}, status=400)

            price = round(price * (1 + tax / 100), 2)
            selling_price = round(selling_price * (1 + tax / 100), 2)
        else:
            tax = 0
            price = round(price, 2)
            selling_price = round(selling_price, 2)

        # --- Create Item ---
        try:
            item = Item.objects.create(
                company=company,
                item_name=item_name,
                item_code=item_code,
                unit=unit,
                quantity=quantity,
                description=description,
                tax_type=tax_type,
                tax=tax,
                price=price,
                selling_price=selling_price
            )

            return Response({
                "msg": "Item created successfully",
                "item_id": item.id
            }, status=201)

        except Exception as e:
            return Response({"error": str(e), "status": 500}, status=500)
# ------------------ INVOICE CREATE ------------------
class CreateSalesInvoiceView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SalesInvoiceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        items_data = request.data.get("items", [])

        # Additional required fields
        payment_mode_id = request.data.get("payment_mode")
        payment_status_id = request.data.get("payment_status")
        payment_type_id = request.data.get("payment_type")
        received_amt = request.data.get("received_amt", 0.0)

        if not all([payment_mode_id, payment_status_id, payment_type_id]):
            return Response({"error": "Missing payment_mode, payment_status, or payment_type"}, status=400)

        try:
            with transaction.atomic():
                payment_mode = PaymentMode.objects.get(id=payment_mode_id)
                payment_status = PaymentStatus.objects.get(id=payment_status_id)
                payment_type = PaymentType.objects.get(id=payment_type_id)

                invoice = SalesInvoice.objects.create(
                    company=data["company"],
                    client=data["client"],
                    invoice_number=data["invoice_number"],
                    final_discount_applicable=data.get("final_discount_applicable", False),
                    final_discount=data.get("final_discount", 0),
                    payment_mode=payment_mode,
                    payment_status=payment_status,
                    payment_type=payment_type,
                    received_amt=received_amt,
                )

                subtotal = 0
                for item_data in items_data:
                    item_id = item_data.get("item")
                    quantity = item_data.get("quantity")
                    discount_applicable = item_data.get("discount_applicable", False)
                    discount = item_data.get("discount", 0)

                    if not all([item_id, quantity]):
                        raise ValueError("Item ID and quantity are required")

                    item = Item.objects.get(id=item_id)

                    if item.quantity < quantity:
                        raise ValueError(
                            f"Not enough stock for item: {item.item_name}. "
                            f"Available: {item.quantity}, Requested: {quantity}"
                        )

                    item.quantity -= quantity
                    item.save()

                    selling_price = item.selling_price or 0
                    line_total = quantity * selling_price
                    if discount_applicable and discount > 0:
                        line_total -= line_total * (discount / 100)

                    line_total = round(line_total, 2)
                    subtotal += line_total

                    SalesInvoiceItem.objects.create(
                        invoice=invoice,
                        item=item,
                        quantity=quantity,
                        discount_applicable=discount_applicable,
                        discount=discount,
                        line_total=line_total
                    )

                invoice.total_price = invoice.apply_final_discount(subtotal)
                invoice.save(update_fields=["total_price"])

                return Response(SalesInvoiceSerializer(invoice).data, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)




class CreatePurchaseInvoiceView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        company_id = data.get('company')
        supplier_name = data.get('supplier_name')
        invoice_number = data.get('invoice_number')
        items = data.get('items', [])

        if not all([company_id, supplier_name, invoice_number, items]):
            return Response({"error": "All invoice fields and at least one item are required"}, status=400)

        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response({"error": "Invalid company ID"}, status=404)

        if PurchaseInvoice.objects.filter(invoice_number=invoice_number).exists():
            return Response({"error": "Invoice number must be unique"}, status=400)

        # Create the invoice
        invoice = PurchaseInvoice.objects.create(
            company=company,
            supplier_name=supplier_name,
            invoice_number=invoice_number,
        )

        total_price = 0

        for item_data in items:
            item_name = item_data.get('item_name')
            unit_id = item_data.get('unit')
            quantity = item_data.get('quantity')
            cost_price = item_data.get('cost_price')

    # 🔴 Check for missing fields
        if not item_name:
            invoice.delete()
            return Response({"error": "Item name is required."}, status=400)

        if not unit_id:
            invoice.delete()
            return Response({"error": f"Unit is required for item '{item_name or 'Unnamed'}'."}, status=400)

        if not quantity:
            invoice.delete()
            return Response({"error": f"Quantity is required for item '{item_name or 'Unnamed'}'."}, status=400)

        if not cost_price:
            invoice.delete()
            return Response({"error": f"Cost price is required for item '{item_name or 'Unnamed'}'."}, status=400)

    # 🔴 Check if Unit ID is valid
        try:
            unit = Unit.objects.get(id=unit_id)
        except Unit.DoesNotExist:
            invoice.delete()
            return Response({"error": f"Invalid unit ID '{unit_id}' for item '{item_name}'."}, status=404)

            # Calculate line total
        line_total = round(quantity * cost_price, 2)
        total_price += line_total

        # Handle item creation/update in Item table
        existing_items = Item.objects.filter(item_name=item_name, company=company)
        matched_item = None
        for item in existing_items:
            if round(item.price, 2) == round(cost_price, 2):
                matched_item = item
                break

        if matched_item:
            matched_item.quantity += quantity
            matched_item.save()
        else:
            Item.objects.create(
                company=company,
                item_name=item_name,
                item_code=f"{item_name[:3].upper()}_{Item.objects.count() + 1}",
                quantity=quantity,
                unit=unit,
                description="Auto-created from Purchase Invoice",
                tax_type=None,
                tax=None,
                price=cost_price,
                selling_price=round(cost_price * 1.1, 2)
                )

        PurchaseInvoiceItem.objects.create(
                invoice=invoice,
                item_name=item_name,
                unit=unit,
                quantity=quantity,
                cost_price=cost_price,
                line_total=line_total
            )

        invoice.total_price = round(total_price, 2)
        invoice.save(update_fields=["total_price"])

        return Response({
            "msg": "Purchase invoice created successfully",
            "invoice_id": invoice.id,
            "total_price": invoice.total_price
        }, status=201)

class UpdateOwnerView(APIView):
    #permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def put(self, request, pk):
        owner = get_object_or_404(Owner, pk=pk)
        serializer = OwnerSerializer(owner, data=request.data, partial=True)
        if  serializer.is_valid():
            serializer.save()
            return Response({"msg": "Owner updated successfully", "data": serializer.data, "status": 200})
        return Response({"error": serializer.errors, "status": 400}, status=400)

class DeleteOwnerView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def delete(self, request, pk):
        owner = get_object_or_404(Owner, pk=pk)
        owner.delete()
        return Response({"msg": "Owner deleted", "status": 200})

# ------------------ COMPANY UPDATE & DELETE ------------------
class UpdateCompanyView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def put(self, request, pk):
        company = get_object_or_404(Company, pk=pk)
        serializer = CompanySerializer(company, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "Company updated successfully", "data": serializer.data, "status": 200})
        return Response({"error": serializer.errors, "status": 400}, status=400)

class DeleteCompanyView(APIView):
    #permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def delete(self, request, pk):
        company = get_object_or_404(Company, pk=pk)
        company.delete()
        return Response({"msg": "Company deleted", "status": 200})

# ------------------ CLIENT UPDATE & DELETE ------------------
class UpdateClientView(APIView):
    #permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def put(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        serializer = ClientSerializer(client, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "Client updated successfully", "data": serializer.data, "status": 200})
        return Response({"error": serializer.errors, "status": 400}, status=400)

class DeleteClientView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def delete(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        client.delete()
        return Response({"msg": "Client deleted", "status": 200})

# ------------------ ITEM UPDATE & DELETE ------------------
class UpdateItemView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def put(self, request, pk):
        item = get_object_or_404(Item, pk=pk)
        serializer = ItemSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "Item updated successfully", "data": serializer.data, "status": 200})
        return Response({"error": serializer.errors, "status": 400}, status=400)

class DeleteItemView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def delete(self, request, pk):
        item = get_object_or_404(Item, pk=pk)
        item.delete()
        return Response({"msg": "Item deleted", "status": 200})

# ------------------ INVOICE UPDATE & DELETE ------------------
class ListSalesInvoiceView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        invoices = SalesInvoice.objects.filter(deleted=False)
        serializer = SalesInvoiceSerializer(invoices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ListPurchaseInvoiceView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        invoices = PurchaseInvoice.objects.filter(deleted=False)
        serializer = PurchaseInvoiceSerializer(invoices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DeleteSalesInvoiceView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, pk):
        try:
            invoice = SalesInvoice.objects.get(pk=pk,deleted=False)
            items = invoice.items.all()

            for item_entry in items:
                item = item_entry.item
                item.quantity += item_entry.quantity
                item.save()

            invoice.is_deleted = True
            invoice.save(update_fields=['is_deleted'])

            return Response({"detail": "Invoice soft-deleted"}, status=status.HTTP_200_OK)

        except SalesInvoice.DoesNotExist:
            return Response({"error": "Invoice not found or already deleted"}, status=status.HTTP_404_NOT_FOUND)

class DeletePurchaseInvoiceView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, pk):
        try:
            invoice = PurchaseInvoice.objects.get(pk=pk,deleted=False)
            items = invoice.items.all()

            for pi_item in items:
                from company.models import Item
                matching_items = Item.objects.filter(
                    item_name=pi_item.item_name,
                    company=invoice.company,
                    unit=pi_item.unit
                )
                for item in matching_items:
                    item.quantity -= pi_item.quantity
                    item.quantity = max(0, item.quantity)
                    item.save()

            invoice.deleted = True
            invoice.save(update_fields=['deleted'])

            return Response({"detail": "Purchase invoice soft-deleted"}, status=status.HTTP_200_OK)

        except PurchaseInvoice.DoesNotExist:
            return Response({"error": "Invoice not found or already deleted"}, status=status.HTTP_404_NOT_FOUND)


# ------------------ LIST & RETRIEVE VIEWS ------------------

class ListOwnersView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def get(self, request):
        owners = Owner.objects.filter(deleted=False)
        serializer = OwnerSerializer(owners, many=True)
        return Response(serializer.data, status=200)

class RetrieveOwnerView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def get(self, request, pk):
        owner = get_object_or_404(Owner, pk=pk,deleted=False)
        serializer = OwnerSerializer(owner)
        return Response(serializer.data, status=200)

class ListCompaniesView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def get(self, request):
        companies = Company.objects.filter(deleted=False)
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data, status=200)

class RetrieveCompanyView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny] 
    def get(self, request, pk):
        company = get_object_or_404(Company, pk=pk,deleted=False)
        serializer = CompanySerializer(company)
        return Response(serializer.data, status=200)

class ListClientsView(APIView):
  #  permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def get(self, request):
        clients = Client.objects.filter(deleted=False)
        serializer = ClientSerializer(clients, many=True)
        return Response(serializer.data, status=200)

class RetrieveClientView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def get(self, request, pk):
        client = get_object_or_404(Client, pk=pk,deleted=False)
        serializer = ClientSerializer(client)
        return Response(serializer.data, status=200)

class ListItemsView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def get(self, request):
        items = Item.objects.filter(deleted=False)
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data, status=200)

class RetrieveItemView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def get(self, request, pk):
        item = get_object_or_404(Item, pk=pk,deleted=False)
        serializer = ItemSerializer(item)
        return Response(serializer.data, status=200)
class RetrieveSalesInvoiceView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            invoice = SalesInvoice.objects.get(pk=pk, deleted=False)
            serializer = SalesInvoiceSerializer(invoice)
            return Response(serializer.data, status=200)
        except SalesInvoice.DoesNotExist:
            return Response({"error": "Sales invoice not found"}, status=404)
        
class RetrievePurchaseInvoiceView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            invoice = PurchaseInvoice.objects.get(pk=pk,deleted=False)
            serializer = PurchaseInvoiceSerializer(invoice)
            return Response(serializer.data, status=200)
        except PurchaseInvoice.DoesNotExist:
            return Response({"error": "Purchase invoice not found"}, status=404)

class UpdateSalesInvoiceView(APIView):
    permission_classes = [AllowAny]

    def put(self, request, pk):
        try:
            invoice = SalesInvoice.objects.get(pk=pk, deleted=False)
        except SalesInvoice.DoesNotExist:
            return Response({"error": "Sales invoice not found"}, status=404)

        # Exclude current invoice from unique check
        invoice_number = request.data.get("invoice_number")
        if invoice_number and SalesInvoice.objects.exclude(pk=pk).filter(invoice_number=invoice_number).exists():
            return Response({"invoice_number": ["sales invoice with this invoice number already exists."]}, status=400)

        serializer = SalesInvoiceSerializer(invoice, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        items_data = request.data.get("items", [])
        try:
            with transaction.atomic():
                # Restore stock for old items
                for item_entry in invoice.items.all():
                    item = item_entry.item
                    item.quantity += item_entry.quantity
                    item.save()
                invoice.items.all().delete()

                subtotal = 0   
                for item_data in items_data:
                    item_id = item_data.get("item")
                    quantity = item_data.get("quantity")
                    discount_applicable = item_data.get("discount_applicable", False)
                    discount = item_data.get("discount", 0)

                    if not all([item_id, quantity]):
                        raise ValidationError("Item ID and quantity are required")

                    item = Item.objects.get(id=item_id)
                    if item.quantity < quantity:
                        raise ValidationError(
                            f"Not enough stock for item: {item.item_name}. "
                            f"Available: {item.quantity}, Requested: {quantity}"
                        )
                    item.quantity -= quantity
                    item.save()

                    selling_price = item.selling_price or 0
                    line_total = quantity * selling_price
                    if discount_applicable and discount > 0:
                        line_total -= line_total * (discount / 100)
                    line_total = round(line_total, 2)
                    subtotal += line_total

                    SalesInvoiceItem.objects.create(
                        invoice=invoice,
                        item=item,
                        quantity=quantity,
                        discount_applicable=discount_applicable,
                        discount=discount,
                        line_total=line_total
                    )

                serializer.save(total_price=invoice.apply_final_discount(subtotal))
                return Response(SalesInvoiceSerializer(invoice).data, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

class UpdatePurchaseInvoiceView(APIView):
    permission_classes = [AllowAny]

    def put(self, request, pk):
        try:
            invoice = PurchaseInvoice.objects.get(pk=pk, deleted=False)
        except PurchaseInvoice.DoesNotExist:
            return Response({"error": "Purchase invoice not found"}, status=404)

        data = request.data
        items = data.get('items', [])

        if not items:
            return Response({"error": "At least one item is required"}, status=400)

        try:
            with transaction.atomic():
                # STEP 1: Rollback old stock using exact item match (item_name + unit + cost_price)
                for pi_item in invoice.items.all():
                    try:
                        matched_item = Item.objects.get(
                            item_name=pi_item.item_name,
                            unit=pi_item.unit,
                            company=invoice.company,
                            price=pi_item.cost_price
                        )
                    except Item.DoesNotExist:
                        raise ValidationError(
                            f"No matching item found for rollback: {pi_item.item_name} at price {pi_item.cost_price}"
                        )

                    if matched_item.quantity < pi_item.quantity:
                        raise ValidationError(
                            f"Cannot update invoice: Not enough stock to remove for item '{matched_item.item_name}'. "
                            f"Current stock: {matched_item.quantity}, to remove: {pi_item.quantity}"
                        )

                    matched_item.quantity -= pi_item.quantity
                    matched_item.save()

                invoice.items.all().delete()

                # STEP 2: Add new items
                total_price = 0
                for item_data in items:
                    item_name = item_data.get('item_name')
                    unit_id = item_data.get('unit')
                    quantity = item_data.get('quantity')
                    cost_price = item_data.get('cost_price')

                    if not item_name or not unit_id or quantity in [None, "", 0] or cost_price in [None, "", 0]:
                        raise ValidationError("All item fields are required and must be greater than zero.")

                    try:
                        quantity = float(quantity)
                        cost_price = float(cost_price)
                    except Exception:
                        raise ValidationError("Quantity and cost price must be valid numbers.")

                    if quantity <= 0:
                        raise ValidationError(f"Quantity must be greater than zero for item: {item_name}")
                    if cost_price <= 0:
                        raise ValidationError(f"Cost price must be greater than zero for item: {item_name}")

                    try:
                        unit = Unit.objects.get(id=unit_id)
                    except Unit.DoesNotExist:
                        raise ValidationError(f"Invalid unit ID '{unit_id}' for item '{item_name}'.")

                    line_total = round(quantity * cost_price, 2)
                    total_price += line_total

                    # STEP 2.1: Reuse existing item if same name, company, unit and price match
                    existing_items = Item.objects.filter(
                        item_name=item_name,
                        company=invoice.company,
                        unit=unit,
                        price=cost_price
                    ).order_by('id')

                    if existing_items.exists():
                        matched_item = existing_items.first()
                        matched_item.quantity += quantity
                        matched_item.save()
                    else:
                        matched_item = Item.objects.create(
                            company=invoice.company,
                            item_name=item_name,
                            item_code=f"{item_name[:3].upper()}_{Item.objects.count() + 1}",
                            quantity=quantity,
                            unit=unit,
                            description="Auto-created from Purchase Invoice",
                            tax_type=None,
                            tax=None,
                            price=cost_price,
                            selling_price=round(cost_price * 1.1, 2)
                        )

                    # STEP 2.2: Create PurchaseInvoiceItem
                    PurchaseInvoiceItem.objects.create(
                        invoice=invoice,
                        item_name=item_name,
                        unit=unit,
                        quantity=quantity,
                        cost_price=cost_price,
                        line_total=line_total
                    )

                # STEP 3: Update invoice main fields
                invoice.supplier_name = data.get('supplier_name', invoice.supplier_name)
                invoice.invoice_number = data.get('invoice_number', invoice.invoice_number)
                invoice.total_price = round(total_price, 2)
                invoice.save(update_fields=["supplier_name", "invoice_number", "total_price"])

                return Response(PurchaseInvoiceSerializer(invoice).data, status=200)

        except ValidationError as ve:
            return Response({"error": str(ve)}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400) #outstanding,salesreport person ka name number
        #9322212299
class PaymentInView(APIView):
    def post(self, request):
        data = request.data
        amount = float(data.get('amount'))
        invoice_ids = data.get('invoice_ids', [])
        bank_id = data.get('bank_id')

        if not amount or not invoice_ids or not bank_id:
            return Response({"error": "amount, invoice_ids, and bank_id are required."}, status=400)

        try:
            bank = Bank.objects.get(id=bank_id)
        except Bank.DoesNotExist:
            return Response({"error": "Bank not found."}, status=404)

        with transaction.atomic():
            for invoice_id in invoice_ids:
                try:
                    invoice = SalesInvoice.objects.select_for_update().get(id=invoice_id)
                except SalesInvoice.DoesNotExist:
                    continue

                remaining = invoice.total_price - invoice.received_amt
                if remaining <= 0:
                    continue

                if amount >= remaining:
                    invoice.received_amt += remaining
                    invoice.payment_status_id = 3  # Fully paid
                    amount -= remaining
                else:
                    invoice.received_amt += amount
                    invoice.payment_status_id = 2  # Partially paid
                    amount = 0

                invoice.save(update_fields=['received_amt', 'payment_status'])

                if amount <= 0:
                    break

            # Update bank balance with transaction
            BankTransaction.objects.create(
                bank=bank,
                company=bank.company,
                amount=data['amount'],
                transaction_type='credit',
                description=f"Payment received for invoices: {invoice_ids}"
            )

        return Response({"status": 200, "message": "Payment applied successfully."})


class PaymentOutView(APIView):
    def post(self, request):
        data = request.data
        amount = float(data.get('amount'))
        invoice_ids = data.get('invoice_ids', [])
        bank_id = data.get('bank_id')

        if not amount or not invoice_ids or not bank_id:
            return Response({"error": "amount, invoice_ids, and bank_id are required."}, status=400)

        try:
            bank = Bank.objects.get(id=bank_id)
        except Bank.DoesNotExist:
            return Response({"error": "Bank not found."}, status=404)

        with transaction.atomic():
            for invoice_id in invoice_ids:
                try:
                    invoice = PurchaseInvoice.objects.select_for_update().get(id=invoice_id)
                except PurchaseInvoice.DoesNotExist:
                    continue

                remaining = invoice.total_price - invoice.paid_amt
                if remaining <= 0:
                    continue

                if amount >= remaining:
                    invoice.paid_amt += remaining
                    invoice.payment_status_id = 3  # Fully paid
                    amount -= remaining
                else:
                    invoice.paid_amt += amount
                    invoice.payment_status_id = 2  # Partially paid
                    amount = 0

                invoice.save(update_fields=['paid_amt', 'payment_status'])

                if amount <= 0:
                    break

            # Deduct from bank balance
            BankTransaction.objects.create(
                bank=bank,
                company=bank.company,
                amount=data['amount'],
                transaction_type='debit',
                description=f"Payment made for purchase invoices: {invoice_ids}"
            )

        return Response({"status": 200, "message": "Payment applied and bank debited successfully."})
