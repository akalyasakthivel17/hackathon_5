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
from datetime import datetime, timedelta, timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.hashers import check_password
import json
from bson import ObjectId
from .models import Employee





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
            office_mail=data.get("office_mail")
            role = data.get("role", "USER")
            documents = data.get("documents", [])

            # Generate EMP001, EMP002, ...
            emp_id = generate_employee_id()

            # generate random password
            password = generate_password()

            employee_data = {
                "emp_id": emp_id,
                "name": name,
                "dob": dob,
                "department": data.get("department"),
                "email": email,
                "office_mail":office_mail,
                "role":role,
                "documents": documents,
                "password": password,
                "created_date": datetime.now(),
                "modified_date": datetime.now(),
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
Email: {office_mail}
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
    # def get(self, request, emp_oid=None):
    #     try:
    #         collection = db["employees"]
    #         if emp_oid:
                
    #             emp = collection.find_one(
    #                 {"_id": ObjectId(emp_oid), "deleted_yn": 0},
    #                 {"_id": 0}
    #             )

    #             if not emp:
    #                 return JsonResponse({"status": "error", "message": "Employee not found"}, status=404)

    #             return JsonResponse({"status": "success", "employee": emp}, status=200)

    #         # GET all employees
    #         employees = list(collection.find({"deleted_yn": 0}, {"_id": 0}))
    #         return JsonResponse({"status": "success", "employees": employees}, status=200)

    #     except Exception as e:
    #         return JsonResponse({"status": "error", "message": str(e)}, status=500)
    def get(self, request, emp_oid=None):
        try:
            collection = db["employees"]

            if emp_oid:
                emp = collection.find_one(
                    {"_id": ObjectId(emp_oid), "deleted_yn": 0},
                    {"_id": 1, "emp_id": 1, "name": 1, "dob": 1, "email": 1,"office_mail":1,"department":1,
                    "role":1,"documents": 1, "password": 1, "created_date": 1,
                    "modified_date": 1, "deleted_yn": 1}
                )

                if not emp:
                    return JsonResponse({"status": "error", "message": "Employee not found"}, status=404)

                # Convert ObjectId to string
                emp["emp_oid"] = str(emp["_id"])
                del emp["_id"]

                return JsonResponse({"status": "success", "employee": emp}, status=200)

            # GET all employees
            employees = list(
                collection.find(
                    {"deleted_yn": 0},
                    {"_id": 1, "emp_id": 1, "name": 1, "dob": 1, "email": 1,"office_mail":1,
                    "department":1,"role":1,"documents": 1, "password": 1, "created_date": 1,
                    "modified_date": 1, "deleted_yn": 1}
                )
            )

            # Convert OID for all
            for emp in employees:
                emp["emp_oid"] = str(emp["_id"])
                del emp["_id"]

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
                    "updated_at": datetime.now()
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

import hashlib
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@method_decorator(csrf_exempt, name='dispatch')
class SignIn(APIView):
    def post(self, request):
        collection=db["employees"]
        try:
            body = json.loads(request.body.decode())
            email = body.get("email")
            password = body.get("password")

            if not email or not password:
                return JsonResponse({"status": "error", "message": "Email and password required"}, status=400)

            hashed_pw = hash_password(password)

            # Check employee in MongoDB
            emp = collection.find_one({"office_mail": email, "password": password, "deleted_yn": 0})

            if not emp:
                return JsonResponse({"status": "error", "message": "Invalid credentials"}, status=400)

            # Create login session (optional)
            session_token = hashlib.sha256(f"{email}{datetime.now()}".encode()).hexdigest()

            db["sessions"].insert_one({
                "id": str(ObjectId(emp["_id"])),
                "emp_id": emp["emp_id"],
                "email": email,
                "session_token": session_token,
                "login_time": datetime.now()
            })

            return JsonResponse({
                "status": "success",
                "message": "Login successful",
                "data": {
                    "id": str(ObjectId(emp["_id"])),
                    "emp_id": emp["emp_id"],
                    "name": emp["name"],
                    "role": emp.get("role", "EMPLOYEE"),
                    "email": email,
                    "session_token": session_token
                }
            })

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

class SignOut(APIView):
    def post(self, request):
        try:
            body = json.loads(request.body.decode())
            session_token = body.get("session_token")

            if not session_token:
                return JsonResponse({"status": "error", "message": "session_token required"}, status=400)

            # delete session from DB
            db["sessions"].delete_one({"session_token": session_token})

            return JsonResponse({"status": "success", "message": "Logout successful"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

class GrievanceAPI(APIView):
    def post(self, request):
        try:
            collection = db["grievances"]

            # Safely parse JSON body
            try:
                payload = json.loads(request.body.decode("utf-8"))
            except json.JSONDecodeError:
                return JsonResponse(
                    {"status": "error", "message": "Invalid JSON body"},
                    status=400
                )

            category = payload.get("category")
            priority = payload.get("priority")
            subject = payload.get("subject")
            description = payload.get("description")
            status = payload.get("status", "OPEN")
            user_id = payload.get("user_id")

            # Basic validation
            missing = []
            for field_name, value in [
                ("category", category),
                ("priority", priority),
                ("subject", subject),
                ("description", description),
            ]:
                if value in (None, "", []):
                    missing.append(field_name)

            if missing:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": f"Missing required fields: {', '.join(missing)}",
                    },
                    status=400,
                )

            valid_priorities = {"LOW", "MEDIUM", "HIGH"}
            if str(priority).upper() not in valid_priorities:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": f"Invalid priority. Valid values: {sorted(valid_priorities)}",
                    },
                    status=400,
                )

            now = datetime.now()
            grievance_data = {
                "category": category,
                "priority": str(priority).upper(),
                "subject": subject,
                "description": description,
                "status": status,
                "user_id": user_id,
                "created_date": now,
                "modified_date": now,
            }

            # Insert and capture inserted_id
            result = collection.insert_one(grievance_data)
            inserted_id = result.inserted_id

            # Convert ObjectId to string if needed
            inserted_id_str = str(inserted_id) if ObjectId and isinstance(inserted_id, ObjectId) else inserted_id

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Grievance created",
                    "id": inserted_id_str,
                },
                status=201,
            )

        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=500,
            )
    
    
# class GetGrievanceView(APIView):

#     def get(self, request, user_id):
#         grievance_col = db["grievances"]
#         employee_col = db["employees"]
#         try:
#             # ----------------------------
#             # 1️⃣ Fetch employee role 
#             # ----------------------------
#             user = employee_col.find_one({"_id": ObjectId(user_id)})

#             if not user:
#                 return Response({
#                     "status": "error",
#                     "message": "Invalid user_id"
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             user_role = user.get("role", "").lower()  # user / hr

#             # ----------------------------
#             # 2️⃣ Build MongoDB query
#             # ----------------------------
#             query = {}

#             # USER → only their grievances
#             if user_role == "user":
#                 query["user_id"] = user_id

#             # HR → see all grievances (no filter)
#             elif user_role == "hr":
#                 query = {}  # no restriction

#             else:
#                 return Response({
#                     "status": "error",
#                     "message": "Unauthorized role"
#                 }, status=status.HTTP_403_FORBIDDEN)

#             # ----------------------------
#             # 3️⃣ Apply status filter
#             # ----------------------------
#             status_filter = request.GET.get("status", None)
#             if status_filter:
#                 query["status"] = status_filter.upper()

#             # ----------------------------
#             # 4️⃣ Fetch from MongoDB
#             # ----------------------------
#             grievances = list(grievance_col.find(query))

#             # ----------------------------
#             # 5️⃣ Format response
#             # ----------------------------
#             output = []
#             for g in grievances:
#                 output.append({
#                     "_id": str(g["_id"]),
#                     "category": g.get("category"),
#                     "priority": g.get("priority"),
#                     "subject": g.get("subject"),
#                     "description": g.get("description"),
#                     "status": g.get("status"),
#                     "user_id": g.get("user_id"),
#                     "created_date": g.get("created_date"),
#                     "modified_date": g.get("modified_date"),
#                 })

#             return Response({
#                 "status": "success",
#                 "count": len(output),
#                 "data": output
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response({
#                 "status": "error",
#                 "message": str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetGrievanceView(APIView):
    def get(self, request, user_id):
        grievance_col = db["grievances"]
        employee_col = db["employees"]

        try:
            # ----------------------------
            # 1️⃣ Validate employee
            # ----------------------------
            user = employee_col.find_one({"_id": ObjectId(user_id)})

            if not user:
                return Response({
                    "status": "error",
                    "message": "Invalid user_id"
                }, status=status.HTTP_400_BAD_REQUEST)

            user_role = user.get("role", "").lower()

            # ----------------------------
            # 2️⃣ Build query based on role
            # ----------------------------
            if user_role == "user":
                query = {"user_id": user_id}

            elif user_role == "hr":
                query = {}

            elif user_role == "manager":
                from datetime import datetime, timedelta

                hr_users = employee_col.find(
                    {"role": {"$regex": "^hr$", "$options": "i"}},
                    {"_id": 1}
                )
                hr_ids = [str(u["_id"]) for u in hr_users]

                seven_days_ago = datetime.utcnow() - timedelta(days=7)

                query = {
                    "$or": [
                        {"user_id": {"$in": hr_ids}},
                        {"created_date": {"$lte": seven_days_ago}}
                    ]
                }

            else:
                return Response({
                    "status": "error",
                    "message": "Unauthorized role"
                }, status=status.HTTP_403_FORBIDDEN)

            # ----------------------------
            # 3️⃣ Status filter (optional)
            # ----------------------------
            status_filter = request.GET.get("status")
            if status_filter:
                query["status"] = status_filter.upper()

            # ----------------------------
            # 4️⃣ Fetch grievances
            # ----------------------------
            grievances = list(grievance_col.find(query))

            response_data = []

            # ----------------------------
            # 5️⃣ Build response
            # ----------------------------
            for g in grievances:

                # 🔹 Fetch grievance raiser name
                raiser = employee_col.find_one(
                    {"_id": ObjectId(g.get("user_id"))},
                    {"name": 1, "role": 1}
                )

                grievance_obj = {
                    "grievance_id": str(g["_id"]),
                    "category": g.get("category"),
                    "priority": g.get("priority"),
                    "subject": g.get("subject"),
                    "description": g.get("description"),
                    "status": g.get("status"),
                    "raised_by": raiser.get("name") if raiser else "Unknown",
                    "raised_by_role": raiser.get("role") if raiser else "Unknown",
                    "created_date": g.get("created_date"),
                    "modified_date": g.get("modified_date"),
                    "replies": []
                }

                # 🔹 Combine all replies
                for r in g.get("replies", []):

                    reply_user = employee_col.find_one(
                        {"_id": ObjectId(r.get("user_id"))},
                        {"name": 1, "role": 1}
                    )

                    grievance_obj["replies"].append({
                        "comment": r.get("comment"),
                        "replied_by": reply_user.get("name") if reply_user else "Unknown",
                        "replied_by_role": reply_user.get("role") if reply_user else "Unknown",
                        "replied_date": r.get("created_date")
                    })

                response_data.append(grievance_obj)

            return Response({
                "status": "success",
                "count": len(response_data),
                "data": response_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # def get(self, request, user_id):
    #     grievance_col = db["grievances"]
    #     employee_col = db["employees"]

    #     try:
    #         # 1️⃣ Fetch employee role
    #         user = employee_col.find_one({"_id": ObjectId(user_id)})

    #         if not user:
    #             return Response({
    #                 "status": "error",
    #                 "message": "Invalid user_id"
    #             }, status=status.HTTP_400_BAD_REQUEST)

    #         user_role = user.get("role", "").lower()  # user / hr / manager

    #         # 2️⃣ Build base query
    #         query = {}

    #         # USER → only their grievances
    #         if user_role == "user":
    #             query["user_id"] = user_id

    #         # HR → see all grievances
    #         elif user_role == "hr":
    #             query = {}

    #         # MANAGER → HR-raised grievances + grievances older than 7 days
    #         elif user_role == "manager":

    #             # Fetch list of HR employee IDs
    #             hr_users = list(employee_col.find({"role": "HR"}, {"_id": 1}))
    #             hr_ids = [str(u["_id"]) for u in hr_users]

    #             # 7-Day old date
    #             from datetime import datetime, timedelta
    #             seven_days_ago = datetime.now() - timedelta(days=7)

    #             # Manager logic: OR condition
    #             query = {
    #                 "$or": [
    #                     {"user_id": {"$in": hr_ids}},                    # HR raised grievances
    #                     {"created_date": {"$lte": seven_days_ago}}       # 7 days older grievances
    #                 ]
    #             }

    #         else:
    #             return Response({
    #                 "status": "error",
    #                 "message": "Unauthorized role"
    #             }, status=status.HTTP_403_FORBIDDEN)

    #         # 3️⃣ Apply status filter (optional)
    #         status_filter = request.GET.get("status", None)
    #         if status_filter:
    #             # If manager → status must be nested into OR conditions
    #             if user_role == "manager":
    #                 query = {
    #                     "$and": [
    #                         query,
    #                         {"status": status_filter.upper()}
    #                     ]
    #                 }
    #             else:
    #                 query["status"] = status_filter.upper()

    #         # 4️⃣ Fetch grievances
    #         grievances = list(grievance_col.find(query))

    #         # 5️⃣ Format response
    #         output = []
    #         for g in grievances:
    #             output.append({
    #                 "_id": str(g["_id"]),
    #                 "category": g.get("category"),
    #                 "priority": g.get("priority"),
    #                 "subject": g.get("subject"),
    #                 "description": g.get("description"),
    #                 "status": g.get("status"),
    #                 "user_id": g.get("user_id"),
    #                 "created_date": g.get("created_date"),
    #                 "modified_date": g.get("modified_date"),
    #             })

    #         return Response({
    #             "status": "success",
    #             "count": len(output),
    #             "data": output
    #         }, status=status.HTTP_200_OK)

    #     except Exception as e:
    #         return Response({
    #             "status": "error",
    #             "message": str(e)
    #         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HRReplyGrievanceView(APIView):

    def post(self, request, grievance_id, hr_id):
        try:
            employee_col = db["employees"]
            grievance_col = db["grievances"]
            # -----------------------------------------
            # 1️⃣ Validate HR user
            # -----------------------------------------
            hr_user = employee_col.find_one({"_id": ObjectId(hr_id)})

            if not hr_user:
                return Response({"status": "error", "message": "Invalid HR user id"},
                                status=status.HTTP_400_BAD_REQUEST)

            if hr_user.get("role", "").lower() != "hr":
                return Response({"status": "error", "message": "Only HR can reply to grievances"},
                                status=status.HTTP_403_FORBIDDEN)

            # -----------------------------------------
            # 2️⃣ Read inputs
            # -----------------------------------------
            reply_text = request.data.get("reply", "")
            new_status = request.data.get("status", None)   # optional

            if not reply_text:
                return Response({"status": "error", "message": "Reply message required"},
                                status=status.HTTP_400_BAD_REQUEST)

            # -----------------------------------------
            # 3️⃣ Find existing grievance
            # -----------------------------------------
            grievance = grievance_col.find_one({"_id": ObjectId(grievance_id)})

            if not grievance:
                return Response({"status": "error", "message": "Invalid grievance_id"},
                                status=status.HTTP_400_BAD_REQUEST)

            # -----------------------------------------
            # 4️⃣ Prepare comment object
            # -----------------------------------------
            comment = {
                "by": "HR",
                "hr_id": hr_id,
                "reply": reply_text,
                "created_date": str(datetime.now())
            }

            # -----------------------------------------
            # 5️⃣ Append reply to comments list
            # -----------------------------------------
            existing_comments = grievance.get("comments", [])
            existing_comments.append(comment)

            # -----------------------------------------
            # 6️⃣ Update grievance status
            # -----------------------------------------
            update_data = {
                "comments": existing_comments,
                "modified_date": str(datetime.now()),
            }

            if new_status:
                update_data["status"] = new_status.upper()

            grievance_col.update_one(
                {"_id": ObjectId(grievance_id)},
                {"$set": update_data}
            )

            return Response({
                "status": "success",
                "message": "HR reply added successfully",
                "data": update_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"status": "error", "message": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class TaskCreateAssignAPI(APIView):

    def post(self, request):
        try:
            task_col = db["tasks"]
            employee_col = db["employees"]
            data = request.data

            # ----------------------------
            # 1️⃣ Validate Required Fields
            # ----------------------------
            required_fields = ["title", "description", "assigned_to", "due_date"]
            missing = [field for field in required_fields if field not in data]

            if missing:
                return Response({
                    "status": "error",
                    "message": f"Missing fields: {', '.join(missing)}"
                }, status=status.HTTP_400_BAD_REQUEST)

            # ----------------------------
            # 2️⃣ Validate Employee Exists
            # ----------------------------
            employee_id = data["assigned_to"]

            emp = employee_col.find_one({"_id": ObjectId(employee_id), "deleted_yn": 0})
            if not emp:
                return Response({
                    "status": "error",
                    "message": "Assigned employee does not exist"
                }, status=status.HTTP_404_NOT_FOUND)

            # ----------------------------
            # 3️⃣ Handle Initial Comment
            # ----------------------------
            comments_list = []
            if data.get("comment"):
                comments_list.append({
                    "comment_text": data["comment"],
                    "commented_by": data.get("created_by"),
                    "commented_date": datetime.now()
                })

            # ----------------------------
            # 4️⃣ Prepare Task Document
            # ----------------------------
            task_data = {
                "title": data["title"],
                "description": data["description"],
                "assigned_to": employee_id,
                "status": "ASSIGNED",  # INITIAL STATUS
                "priority": data.get("priority", "MEDIUM"),
                "due_date": datetime.fromisoformat(data["due_date"]),
                "created_by": data.get("created_by"),
                "comments": comments_list,
                "created_date": datetime.now(),
                "modified_date": datetime.now(),
                "deleted_yn": 0
            }

            # ----------------------------
            # 5️⃣ Insert into MongoDB
            # ----------------------------
            result = task_col.insert_one(task_data)
            task_data["_id"] = str(result.inserted_id)

            return Response({
                "status": "success",
                "message": "Task created and assigned successfully",
                "task": task_data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class UpdateTaskView(APIView):
    def put(self, request, task_id):
        try:
            task_col = db["tasks"]

            # ----------------------------------------
            # 1️⃣ Fetch task
            # ----------------------------------------
            task = task_col.find_one({"_id": ObjectId(task_id)})

            if not task:
                return Response({
                    "status": "error",
                    "message": "Task not found"
                }, status=status.HTTP_404_NOT_FOUND)

            # ----------------------------------------
            # 2️⃣ Extract update fields
            # ----------------------------------------
            new_status = request.data.get("status")
            comment = request.data.get("comment")
            manager_rating = request.data.get("manager_rating")  # only for COMPLETED
            reassign_to = request.data.get("reassign_to")

            update_data = {
                "modified_date": datetime.utcnow()
            }

            # ----------------------------------------
            # 3️⃣ Handle Status Change
            # ----------------------------------------
            if new_status:
                update_data["status"] = new_status.upper()

            # ----------------------------------------
            # 4️⃣ Handle Comment Append
            # ----------------------------------------
            if comment:
                existing_comments = task.get("comments", [])
                existing_comments.append({
                    "comment": comment,
                    "timestamp": datetime.utcnow().isoformat()
                })
                update_data["comments"] = existing_comments

            # ----------------------------------------
            # 5️⃣ Handle Reassign Employee
            # ----------------------------------------
            if reassign_to:
                update_data["assigned_to"] = reassign_to
                update_data["status"] = "ASSIGNED"

            # ----------------------------------------
            # 6️⃣ Automated Final Scoring (Triggered on COMPLETED)
            # ----------------------------------------
            final_score = None
            final_reason = None

            if new_status and new_status.upper() == "COMPLETED":

                # --------------------------
                # Deadline Parsing (❗fixed)
                # --------------------------
                deadline_str = task.get("deadline", None)
                on_time = False

                try:
                    if deadline_str:
                        # Convert stored string → datetime
                        deadline_dt = datetime.fromisoformat(deadline_str.replace("Z", ""))
                        on_time = datetime.now() <= deadline_dt
                except:
                    # If invalid date format → treat as "not on time"
                    on_time = False

                # Scoring
                score = 0

                # Manager rating → 50%
                if manager_rating:
                    score += (manager_rating * 10)

                # Deadline score → 30%
                if on_time:
                    score += 30
                else:
                    score += 10

                # Comment-based quality → 20%
                if comment and ("completed" in comment.lower() or "done" in comment.lower()):
                    score += 20
                else:
                    score += 10

                final_score = min(score, 100)

                # Reason
                reason_list = []
                if manager_rating:
                    reason_list.append(f"Manager rating contributed {manager_rating * 10} points.")
                if on_time:
                    reason_list.append("Task was completed before deadline (+30).")
                else:
                    reason_list.append("Task was completed after deadline (-20).")
                if comment:
                    reason_list.append("Comment indicated completion quality (+20).")

                final_reason = " ".join(reason_list)

                update_data["final_score"] = final_score
                update_data["final_reason"] = final_reason

            # ----------------------------------------
            # 7️⃣ Update MongoDB
            # ----------------------------------------
            task_col.update_one(
                {"_id": ObjectId(task_id)},
                {"$set": update_data}
            )

            # ----------------------------------------
            # 8️⃣ Success Response
            # ----------------------------------------
            return Response({
                "status": "success",
                "message": "Task updated successfully",
                "final_score": final_score,
                "score_reason": final_reason
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskListByEmployeeAPI(APIView):

    def get(self, request, emp_id):
        try:
            task_col = db["tasks"]
            # ----------------------------
            # 1️⃣ Validate employee ID
            # ----------------------------
            try:
                ObjectId(emp_id)
            except:
                return Response({
                    "status": "error",
                    "message": "Invalid employee ObjectId"
                }, status=status.HTTP_400_BAD_REQUEST)

            # ----------------------------
            # 2️⃣ Filter tasks assigned to this employee
            # ----------------------------
            tasks = list(task_col.find(
                {
                    "assigned_to": emp_id,
                    "deleted_yn": 0
                }
            ))

            # ----------------------------
            # 3️⃣ Format output
            # ----------------------------
            output = []
            for t in tasks:
                output.append({
                    "task_id": str(t["_id"]),
                    "title": t.get("title"),
                    "description": t.get("description"),
                    "status": t.get("status"),
                    "priority": t.get("priority"),
                    "assigned_to": t.get("assigned_to"),
                    "due_date": t.get("due_date"),
                    "comments": t.get("comments", []),
                    "final_score": t.get("final_score"),
                    "final_reason": t.get("final_reason"),
                    "created_date": t.get("created_date"),
                    "modified_date": t.get("modified_date")
                })

            return Response({
                "status": "success",
                "count": len(output),
                "tasks": output
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class TaskDeleteAPI(APIView):

    def delete(self, request, task_id):
        try:
            task_col = db["tasks"]
            # ----------------------------
            # 1️⃣ Validate Task ID
            # ----------------------------
            try:
                oid = ObjectId(task_id)
            except:
                return Response({
                    "status": "error",
                    "message": "Invalid task ObjectId"
                }, status=status.HTTP_400_BAD_REQUEST)

            # ----------------------------
            # 2️⃣ Fetch Task
            # ----------------------------
            task = task_col.find_one({"_id": oid, "deleted_yn": 0})

            if not task:
                return Response({
                    "status": "error",
                    "message": "Task not found or already deleted"
                }, status=status.HTTP_404_NOT_FOUND)

            # ----------------------------
            # 3️⃣ Soft Delete Action
            # ----------------------------
            task_col.update_one(
                {"_id": oid},
                {
                    "$set": {
                        "deleted_yn": 1,
                        "modified_date": datetime.utcnow()
                    }
                }
            )

            return Response({
                "status": "success",
                "message": "Task deleted successfully (soft delete)"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class empoyeedropdown(APIView):
    def get(self, request, emp_oid=None):
        try:
            collection = db["employees"]

            if emp_oid:
                emp = collection.find_one(
                    {"_id": ObjectId(emp_oid), "deleted_yn": 0},
                    {"_id": 1, "emp_id": 1, "name": 1}
                )

                if not emp:
                    return JsonResponse({"status": "error", "message": "Employee not found"}, status=404)

                # Convert ObjectId to string
                emp["emp_oid"] = str(emp["_id"])
                del emp["_id"]

                return JsonResponse({"status": "success", "employee": emp}, status=200)

            # GET all employees
            employees = list(
                collection.find(
                    {"deleted_yn": 0},
                    {"_id": 1, "emp_id": 1, "name": 1}
                )
            )

            # Convert OID for all
            for emp in employees:
                emp["emp_oid"] = str(emp["_id"])
                del emp["_id"]

            return JsonResponse({"status": "success", "employees": employees}, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

class DashboardAPI(APIView):

    def get(self, request, user_id):
        try:
            employee_col = db["employees"]
            task_col = db["tasks"]

            # --------------------------------------
            # 1️⃣ Validate Employee
            # --------------------------------------
            try:
                emp_oid = ObjectId(user_id)
            except:
                return Response({
                    "status": "error",
                    "message": "Invalid user_id"
                }, status=status.HTTP_400_BAD_REQUEST)

            employee = employee_col.find_one({
                "_id": emp_oid,
                "deleted_yn": 0
            })

            if not employee:
                return Response({
                    "status": "error",
                    "message": "Employee not found"
                }, status=status.HTTP_404_NOT_FOUND)

            # --------------------------------------
            # 2️⃣ Active Employee Metrics (GLOBAL)
            # --------------------------------------
            active_employees = list(
                employee_col.find({"deleted_yn": 0})
            )

            department_counts = {}
            for emp in active_employees:
                dept = emp.get("department", "Unknown")
                department_counts[dept] = department_counts.get(dept, 0) + 1

            # --------------------------------------
            # 3️⃣ Task Metrics (USER-SPECIFIC)
            # --------------------------------------
            now = datetime.now()
            month_start = datetime(now.year, now.month, 1)

            tasks = list(task_col.find({
                "assigned_to": user_id,
                "deleted_yn": 0
            }))

            assigned_count = 0
            completed_count = 0

            for task in tasks:
                created_str = task.get("created_date")
                if not created_str:
                    continue

                try:
                    created_dt = datetime.fromisoformat(created_str.replace("Z", ""))
                except:
                    continue

                if created_dt >= month_start:
                    assigned_count += 1
                    if task.get("status", "").upper() == "COMPLETED":
                        completed_count += 1

            remaining_count = assigned_count - completed_count

            # --------------------------------------
            # 4️⃣ Response
            # --------------------------------------
            return Response({
                "status": "success",
                "employee_metrics": {
                    "total_active_employees": len(active_employees),
                    "department_wise_count": department_counts
                },
                "task_metrics": {
                    "assigned_this_month": assigned_count,
                    "completed_this_month": completed_count,
                    "remaining_tasks": remaining_count
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
