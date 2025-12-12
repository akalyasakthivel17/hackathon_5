from django.shortcuts import render
from rest_framework.decorators import api_view
from django.http import JsonResponse
import random
import string
import base64
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bson.objectid import ObjectId
from pymongo import MongoClient
import uuid
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
import json
from bson import ObjectId
# Create your views here.
@api_view(["GET"])
def welcome(request):   
    return JsonResponse({"message": "Welcome to the Resume Scorer python API!"})

# --------------------------
# MongoDB Connection
# --------------------------
client = MongoClient("mongodb+srv://akalyabharath20_db_user:LVyhweJauTGaO0pp@cluster0.2ss7wcx.mongodb.net/")
db = client["test"]
employee_collection = db["employees"]


# --------------------------
# Helper Functions
# --------------------------
def generate_employee_id():
    return f"EMP-{uuid.uuid4().hex[:6].upper()}"


def employee_to_json(emp):
    emp["_id"] = str(emp["_id"])
    return emp
def generate_password(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def encode_file(file):
    """
    Converts uploaded file into base64 string.
    """
    file_content = file.read()
    return base64.b64encode(file_content).decode("utf-8")

def generate_employee_id():
    collection = db["employees"]
    # find last employee WITH emp_id field ONLY
    last_emp = collection.find_one(
        {"emp_id": {"$exists": True}},
        sort=[("emp_id", -1)]
    )

    if not last_emp:
        return "EMP001"

    try:
        last_id = last_emp.get("emp_id", "EMP000")  # safe default
        num = int(last_id.replace("EMP", "")) + 1
        return f"EMP{num:03d}"
    except:
        # fallback if corrupted data exists
        count = collection.count_documents({"emp_id": {"$exists": True}})
        return f"EMP{count+1:03d}"



# --------------------------
# 📌 Employee API (CRUD + Documents inside same API)
# --------------------------
@method_decorator(csrf_exempt, name='dispatch')
class EmployeeAPI(APIView):

    # CREATE EMPLOYEE + embedded documents (base64)
#     def post(self, request):
#         data = request.data

#         documents = data.get("documents", [])  # List of dicts

#         employee = {
#             "employee_id": generate_employee_id(),
#             "name": data.get("name"),
#             "department": data.get("department"),
#             "role": data.get("role"),
#             "contact": data.get("contact"),
#             "address": data.get("address"),
#             "email": data.get("email"),
#             "dob": data.get("dob"),
#             "joining_date": data.get("joining_date"),
#             "picture": data.get("picture"),  # base64 image

#             "documents": documents,  # base64 documents list

#             # NEW fields
#             "created_at": datetime.now(),
#             "updated_at": datetime.now(),
#             "deleted_yn": 0  # active employee
#         }
#         email=data.get("email")
#         password = generate_password()
#         name=data.get("name")

#         inserted = employee_collection.insert_one(employee)
#         employee["_id"] = str(inserted.inserted_id)
#         # ---------- SEND WELCOME EMAIL ----------
#         subject = "Welcome to the Company"
#         message = f"""
# Hello {name},

# Your employee account has been created successfully.

# Login Details:
# Email: {email}
# Password: {password}

# Please change your password after first login.

# Regards,
# HR Team
# """
#         send_mail(
#             subject,
#             message,
#             "akalyabharath20@gmail.com",
#             [email],
#             fail_silently=False,
#         )

#         return Response(employee, status=status.HTTP_201_CREATED)
    def post(self, request):
        try:
            collection = db["employees"]
            data = json.loads(request.body.decode('utf-8'))

            name = data.get("name")
            dob = data.get("dob")
            email = data.get("email")
            documents = data.get("documents", [])

            # Generate EMP001, EMP002, ...
            emp_id = generate_employee_id()

            # generate random password
            password = generate_password()

            employee_data = {
                "emp_id": emp_id,
                "name": name,
                "dob": dob,
                "email": email,
                "documents": documents,
                "password": password,
                "created_date": datetime.utcnow(),
                "modified_date": datetime.utcnow(),
                "deleted_yn": 0
            }

            collection.insert_one(employee_data)

            # ------------------------
            # SEND WELCOME EMAIL
            # ------------------------
            subject = "Welcome to the Company"
            text_message = f"""
Hello {name},

Your employee account has been created.

Employee ID: {emp_id}
Email: {email}
Password: {password}

Please change your password on first login.

Regards,
HR Team
"""

            try:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_message,
                    from_email="akalyabharath20@gmail.com",
                    to=[email]
                )
                msg.send()
            except Exception as mail_error:
                return JsonResponse({
                    "status": "warning",
                    "message": "Employee created but email not sent",
                    "mail_error": str(mail_error)
                }, status=207)

            return JsonResponse({
                "status": "success",
                "message": "Employee added and welcome mail sent",
                "emp_id": emp_id
            }, status=201)

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    # GET All active employees or search
    def get(self, request, emp_oid=None):
        try:
            collection = db["employees"]
            if emp_oid:
                
                emp = collection.find_one(
                    {"_id": ObjectId(emp_oid), "deleted_yn": 0},
                    {"_id": 0}
                )

                if not emp:
                    return JsonResponse({"status": "error", "message": "Employee not found"}, status=404)

                return JsonResponse({"status": "success", "employee": emp}, status=200)

            # GET all employees
            employees = list(collection.find({"deleted_yn": 0}, {"_id": 0}))
            return JsonResponse({"status": "success", "employees": employees}, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


    # UPDATE employee
    def put(self, request):
        emp_id = request.GET.get("id")

        if not emp_id:
            return Response({"error": "Employee ID missing"}, 400)

        update_fields = request.data
        update_fields["updated_at"] = datetime.utcnow()

        employee_collection.update_one(
            {"_id": ObjectId(emp_id)},
            {"$set": update_fields}
        )

        return Response({"message": "Employee updated"}, 200)

    # SOFT DELETE employee
    def delete(self, request):
        emp_id = request.GET.get("id")

        if not emp_id:
            return Response({"error": "Employee ID missing"}, 400)

        employee_collection.update_one(
            {"_id": ObjectId(emp_id)},
            {
                "$set": {
                    "deleted_yn": 1,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return Response({"message": "Employee soft deleted"}, 200)

class EmployeeUpdateView(APIView):
    collection = db["employees"]

    @method_decorator(csrf_exempt, name="dispatch")
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def put(self, request, emp_oid):
        try:
            collection = db["employees"]
            data = json.loads(request.body.decode('utf-8'))

            update_data = {
                "name": data.get("name"),
                "dob": data.get("dob"),
                "email": data.get("email"),
                "documents": data.get("documents", []),
                "modified_date": datetime.now()
            }

            # Remove empty values
            update_data = {k: v for k, v in update_data.items() if v is not None}

            result = collection.update_one(
                {"_id": ObjectId(emp_oid), "deleted_yn": 0},
                {"$set": update_data}
            )

            if result.matched_count == 0:
                return JsonResponse({"status": "error", "message": "Employee not found"}, status=404)

            return JsonResponse({"status": "success", "message": "Employee updated successfully"}, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
        
class EmployeeDeleteView(APIView):

    @method_decorator(csrf_exempt, name="dispatch")
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def delete(self, request, emp_oid):
        collection = db["employees"]
        try:
            result = collection.update_one(
                {"_id": ObjectId(emp_oid), "deleted_yn": 0},
                {"$set": {
                    "deleted_yn": 1,
                    "modified_date": datetime.now()
                }}
            )

            if result.matched_count == 0:
                return JsonResponse({"status": "error", "message": "Employee not found or already deleted"}, status=404)

            return JsonResponse({"status": "success", "message": "Employee soft deleted"}, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

