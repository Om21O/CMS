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
    # permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        owner_id = data.get('owner_id')
        company_name = data.get('company_name')
        phone_no = data.get('phone_no')
        gst = data.get('gst')
        address = data.get('address')
        type_of_company = data.get('type_of_company')

        if not all([owner_id, company_name, phone_no, gst, address]):
            return Response({"error": "Missing required fields", "status": 400}, status=400)

        try:
            owner = Owner.objects.get(id=owner_id)
        except Owner.DoesNotExist:
            return Response({"error": "Owner not found", "status": 404}, status=404)

        limit = 3 if owner.type_of_company == 'basic' else 5
        current = Company.objects.filter(owner=owner).count()

        if current >=limit:
            return Response({
                "error": f"{owner.type_of_company} plan allows only {limit} companies",
                "status": 400
            }, status=400)

        try:
            company = Company.objects.create(
                owner=owner,
                company_name=company_name,
                phone_no=phone_no,
                gst=gst,
                address=address,
                type_of_company=type_of_company
            )

            return Response({
                "msg": "Company created successfully",
                "company_id": company.id
            }, status=201)

        except Exception as e:
            return Response({"error": str(e), "status": 500})

# ------------------ CLIENT CREATE ------------------
class CreateClientView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        company_id = data.get('company_id')
        client_name = data.get('client_name')
        address = data.get('address')
        gst = data.get('gst')
        phone_no = data.get('phone_no')

        if not all([company_id, client_name, address, phone_no]):
            return Response({"error": "Missing required fields", "status": 400}, status=400)

        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response({"error": "Company not found", "status": 404}, status=404)

        try:
            client = Client.objects.create(
                company=company,
                client_name=client_name,
                address=address,
                gst=gst,
                phone_no=phone_no
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
        quantity = float(data.get('quantity', 0))
        description = data.get('description')
        tax_type_id = int(data.get('tax_type'))
        tax = data.get('tax')
        price = float(data.get('price'))
        selling_price = float(data.get('selling_price', 0))  # fallback to price if not set

        if not all([company_id, item_name, item_code, quantity, description, tax_type_id is not None, price]):
            return Response({"error": "Missing required fields", "status": 400}, status=400)

        if quantity <= 0:
            return Response({"error": "Quantity must be greater than zero", "status": 400}, status=400)

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

        
        if tax_type.code == '1':
            if tax is None:
                return Response({"error": "Tax is required for 'withtax' items", "status": 400}, status=400)
            try:
                tax = float(tax)
            except ValueError:
                return Response({"error": "Invalid tax value", "status": 400}, status=400)

            price = round(price * (1 + tax / 100), 2)
            selling_price = round((selling_price or price) * (1 + tax / 100), 2)
        else:
            tax = 0
            price = round(price, 2)
            selling_price = round(selling_price or price, 2)

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

        try:
            with transaction.atomic():
                invoice = SalesInvoice.objects.create(
                    company=data["company"],
                    client=data["client"],
                    invoice_number=data["invoice_number"],
                    final_discount_applicable=data.get("final_discount_applicable", False),
                    final_discount=data.get("final_discount", 0)
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

                    # Deduct quantity
                    item.quantity -= quantity
                    item.save()

                    # Calculate line total
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
        serializer = PurchaseInvoiceSerializer(data=request.data)
        if serializer.is_valid():
            invoice = serializer.save()
            return Response(PurchaseInvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateOwnerView(APIView):
    #permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def put(self, request, pk):
        owner = get_object_or_404(Owner, pk=pk)
        serializer = OwnerSerializer(owner, data=request.data, partial=True)
        if serializer.is_valid():
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
        invoices = SalesInvoice.objects.all()
        serializer = SalesInvoiceSerializer(invoices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ListPurchaseInvoiceView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        invoices = PurchaseInvoice.objects.all()
        serializer = PurchaseInvoiceSerializer(invoices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DeleteSalesInvoiceView(APIView):
    permission_classes = [AllowAny]
    def delete(self, request, pk):
        try:
            invoice = SalesInvoice.objects.get(pk=pk)
            invoice.delete()
            return Response({"detail": "Deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except SalesInvoice.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

class DeletePurchaseInvoiceView(APIView):
    permission_classes = [AllowAny]
    def delete(self, request, pk):
        try:
            invoice = PurchaseInvoice.objects.get(pk=pk)
            invoice.delete()
            return Response({"detail": "Deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except PurchaseInvoice.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

# ------------------ LIST & RETRIEVE VIEWS ------------------

class ListOwnersView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def get(self, request):
        owners = Owner.objects.all()
        serializer = OwnerSerializer(owners, many=True)
        return Response(serializer.data, status=200)

class RetrieveOwnerView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def get(self, request, pk):
        owner = get_object_or_404(Owner, pk=pk)
        serializer = OwnerSerializer(owner)
        return Response(serializer.data, status=200)

class ListCompaniesView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def get(self, request):
        companies = Company.objects.all()
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data, status=200)

class RetrieveCompanyView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny] 
    def get(self, request, pk):
        company = get_object_or_404(Company, pk=pk)
        serializer = CompanySerializer(company)
        return Response(serializer.data, status=200)

class ListClientsView(APIView):
  #  permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def get(self, request):
        clients = Client.objects.all()
        serializer = ClientSerializer(clients, many=True)
        return Response(serializer.data, status=200)

class RetrieveClientView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def get(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        serializer = ClientSerializer(client)
        return Response(serializer.data, status=200)

class ListItemsView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def get(self, request):
        items = Item.objects.all()
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data, status=200)

class RetrieveItemView(APIView):
   # permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    def get(self, request, pk):
        item = get_object_or_404(Item, pk=pk)
        serializer = ItemSerializer(item)
        return Response(serializer.data, status=200)

# class ListInvoicesView(APIView):
#    # permission_classes = [AllowAny]
#     permission_classes = [AllowAny]
#     def get(self, request):
#         invoices = Invoice.objects.all()
#         serializer = InvoiceSerializer(invoices, many=True)
#         return Response(serializer.data, status=200)

# class RetrieveInvoiceView(APIView):
#    # permission_classes = [AllowAny]
#     permission_classes = [AllowAny]
#     def get(self, request, pk):
#         invoice = get_object_or_404(Invoice, pk=pk)
#         serializer = InvoiceSerializer(invoice)
#         return Response(serializer.data, status=200)