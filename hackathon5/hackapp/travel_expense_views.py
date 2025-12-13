from rest_framework.views import APIView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import json
import base64

# MongoDB Connection
client = MongoClient("mongodb+srv://akalyabharath20_db_user:LVyhweJauTGaO0pp@cluster0.2ss7wcx.mongodb.net/")
db = client["test"]
employee_collection = db["employees"]
travel_collection = db["travel_requests"]
expense_collection = db["expenses"]


# --------------------------
# HELPER FUNCTIONS
# --------------------------
def generate_travel_id():
    """Generate sequential travel ID (TRV001, TRV002, ...)"""
    last_travel = travel_collection.find_one(
        {"travel_id": {"$exists": True}},
        sort=[("travel_id", -1)]
    )
    if not last_travel:
        return "TRV001"
    try:
        num = int(last_travel["travel_id"].replace("TRV", "")) + 1
        return f"TRV{num:03d}"
    except:
        count = travel_collection.count_documents({"travel_id": {"$exists": True}})
        return f"TRV{count+1:03d}"


def generate_expense_id():
    """Generate sequential expense ID (EXP001, EXP002, ...)"""
    last_expense = expense_collection.find_one(
        {"expense_id": {"$exists": True}},
        sort=[("expense_id", -1)]
    )
    if not last_expense:
        return "EXP001"
    try:
        num = int(last_expense["expense_id"].replace("EXP", "")) + 1
        return f"EXP{num:03d}"
    except:
        count = expense_collection.count_documents({"expense_id": {"$exists": True}})
        return f"EXP{count+1:03d}"


# --------------------------
# TRAVEL REQUEST APIs
# --------------------------
@method_decorator(csrf_exempt, name='dispatch')
class TravelRequest(APIView):
    """Submit and list travel requests"""
    
    def post(self, request):
        """Submit travel request"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            emp_id = data.get("emp_id")
            purpose = data.get("purpose")
            destination = data.get("destination")
            from_date = data.get("from_date")  # YYYY-MM-DD
            to_date = data.get("to_date")
            estimated_cost = data.get("estimated_cost", 0)
            travel_mode = data.get("travel_mode", "FLIGHT")  # FLIGHT, TRAIN, BUS, CAR
            
            if not all([emp_id, purpose, destination, from_date, to_date]):
                return JsonResponse({
                    "status": "error",
                    "message": "emp_id, purpose, destination, from_date, and to_date are required"
                }, status=400)
            
            # Verify employee exists
            emp = employee_collection.find_one({"emp_id": emp_id, "deleted_yn": 0})
            if not emp:
                return JsonResponse({
                    "status": "error",
                    "message": "Employee not found"
                }, status=404)
            
            # Validate travel mode
            valid_modes = ["FLIGHT", "TRAIN", "BUS", "CAR"]
            if travel_mode.upper() not in valid_modes:
                return JsonResponse({
                    "status": "error",
                    "message": f"Invalid travel_mode. Use: {', '.join(valid_modes)}"
                }, status=400)
            
            travel_id = generate_travel_id()
            
            travel_data = {
                "travel_id": travel_id,
                "emp_id": emp_id,
                "emp_name": emp.get("name"),
                "emp_role": emp.get("role", "EMPLOYEE"),
                "purpose": purpose,
                "destination": destination,
                "from_date": from_date,
                "to_date": to_date,
                "estimated_cost": float(estimated_cost),
                "travel_mode": travel_mode.upper(),
                "status": "pending",
                "approved_by": None,
                "approved_by_role": None,
                "approved_date": None,
                "rejection_reason": "",
                "created_date": datetime.utcnow(),
                "modified_date": datetime.utcnow(),
                "deleted_yn": 0
            }
            
            travel_collection.insert_one(travel_data)
            
            return JsonResponse({
                "status": "success",
                "message": "Travel request submitted successfully",
                "travel_id": travel_id
            }, status=201)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def get(self, request):
        """List all travel requests"""
        try:
            # Get query parameters
            status_filter = request.GET.get("status")
            emp_id = request.GET.get("emp_id")
            
            query = {"deleted_yn": 0}
            
            if status_filter:
                query["status"] = status_filter.lower()
            
            if emp_id:
                query["emp_id"] = emp_id
            
            travels = list(travel_collection.find(query, {"_id": 0}).sort("created_date", -1))
            
            # Convert datetime to string
            for travel in travels:
                if travel.get("created_date"):
                    travel["created_date"] = travel["created_date"].isoformat()
                if travel.get("modified_date"):
                    travel["modified_date"] = travel["modified_date"].isoformat()
                if travel.get("approved_date"):
                    travel["approved_date"] = travel["approved_date"].isoformat()
            
            return JsonResponse({
                "status": "success",
                "total": len(travels),
                "travel_requests": travels
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class TravelRequestDetail(APIView):
    """Get, update, or cancel specific travel request"""
    
    def get(self, request, travel_id):
        """Get travel request details"""
        try:
            travel = travel_collection.find_one({"travel_id": travel_id, "deleted_yn": 0}, {"_id": 0})
            
            if not travel:
                return JsonResponse({
                    "status": "error",
                    "message": "Travel request not found"
                }, status=404)
            
            # Convert datetime
            if travel.get("created_date"):
                travel["created_date"] = travel["created_date"].isoformat()
            if travel.get("modified_date"):
                travel["modified_date"] = travel["modified_date"].isoformat()
            if travel.get("approved_date"):
                travel["approved_date"] = travel["approved_date"].isoformat()
            
            return JsonResponse({
                "status": "success",
                "travel_request": travel
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def put(self, request, travel_id):
        """Update travel request (before approval)"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            travel = travel_collection.find_one({"travel_id": travel_id, "deleted_yn": 0})
            if not travel:
                return JsonResponse({
                    "status": "error",
                    "message": "Travel request not found"
                }, status=404)
            
            if travel["status"] != "pending":
                return JsonResponse({
                    "status": "error",
                    "message": f"Cannot update {travel['status']} travel request"
                }, status=400)
            
            update_fields = {}
            if "purpose" in data:
                update_fields["purpose"] = data["purpose"]
            if "destination" in data:
                update_fields["destination"] = data["destination"]
            if "from_date" in data:
                update_fields["from_date"] = data["from_date"]
            if "to_date" in data:
                update_fields["to_date"] = data["to_date"]
            if "estimated_cost" in data:
                update_fields["estimated_cost"] = float(data["estimated_cost"])
            if "travel_mode" in data:
                update_fields["travel_mode"] = data["travel_mode"].upper()
            
            update_fields["modified_date"] = datetime.utcnow()
            
            travel_collection.update_one(
                {"travel_id": travel_id},
                {"$set": update_fields}
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Travel request updated successfully"
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def delete(self, request, travel_id):
        """Cancel travel request (soft delete)"""
        try:
            travel = travel_collection.find_one({"travel_id": travel_id, "deleted_yn": 0})
            if not travel:
                return JsonResponse({
                    "status": "error",
                    "message": "Travel request not found"
                }, status=404)
            
            travel_collection.update_one(
                {"travel_id": travel_id},
                {"$set": {"deleted_yn": 1, "modified_date": datetime.utcnow()}}
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Travel request cancelled successfully"
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class TravelApproval(APIView):
    """Approve or reject travel request"""
    
    def post(self, request, travel_id):
        """Approve/reject travel request"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            action = data.get("action")  # approve or reject
            approver_id = data.get("approver_id")
            rejection_reason = data.get("rejection_reason", "")
            
            if not action or not approver_id:
                return JsonResponse({
                    "status": "error",
                    "message": "action and approver_id are required"
                }, status=400)
            
            if action not in ["approve", "reject"]:
                return JsonResponse({
                    "status": "error",
                    "message": "Invalid action. Use 'approve' or 'reject'"
                }, status=400)
            
            # Find travel request
            travel = travel_collection.find_one({"travel_id": travel_id, "deleted_yn": 0})
            if not travel:
                return JsonResponse({
                    "status": "error",
                    "message": "Travel request not found"
                }, status=404)
            
            if travel["status"] != "pending":
                return JsonResponse({
                    "status": "error",
                    "message": f"Travel request already {travel['status']}"
                }, status=400)
            
            # Verify approver exists
            approver = employee_collection.find_one({"emp_id": approver_id, "deleted_yn": 0})
            if not approver:
                return JsonResponse({
                    "status": "error",
                    "message": "Approver not found"
                }, status=404)
            
            approver_role = approver.get("role", "EMPLOYEE").upper()
            
            # Only HR and Manager can approve travel
            if approver_role not in ["HR", "MANAGER"]:
                return JsonResponse({
                    "status": "error",
                    "message": "Only HR and Manager can approve travel requests"
                }, status=403)
            
            # Update travel status
            new_status = "approved" if action == "approve" else "rejected"
            
            travel_collection.update_one(
                {"travel_id": travel_id},
                {
                    "$set": {
                        "status": new_status,
                        "approved_by": approver_id,
                        "approved_by_role": approver_role,
                        "approved_date": datetime.utcnow(),
                        "rejection_reason": rejection_reason if action == "reject" else "",
                        "modified_date": datetime.utcnow()
                    }
                }
            )
            
            return JsonResponse({
                "status": "success",
                "message": f"Travel request {new_status} successfully",
                "travel_id": travel_id,
                "new_status": new_status
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


# --------------------------
# EXPENSE MANAGEMENT APIs
# --------------------------
@method_decorator(csrf_exempt, name='dispatch')
class ExpenseSubmission(APIView):
    """Submit and list expenses"""
    
    def post(self, request):
        """Submit expense with receipt"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            emp_id = data.get("emp_id")
            travel_id = data.get("travel_id")  # Optional
            expense_type = data.get("expense_type", "TRAVEL")  # TRAVEL, FOOD, ACCOMMODATION, TRANSPORT, OTHER
            category = data.get("category")
            amount = data.get("amount")
            expense_date = data.get("expense_date")
            description = data.get("description", "")
            receipt = data.get("receipt")  # {file_name, file_data (base64), file_type}
            
            if not all([emp_id, category, amount, expense_date]):
                return JsonResponse({
                    "status": "error",
                    "message": "emp_id, category, amount, and expense_date are required"
                }, status=400)
            
            # Verify employee exists
            emp = employee_collection.find_one({"emp_id": emp_id, "deleted_yn": 0})
            if not emp:
                return JsonResponse({
                    "status": "error",
                    "message": "Employee not found"
                }, status=404)
            
            # Validate expense type
            valid_types = ["TRAVEL", "FOOD", "ACCOMMODATION", "TRANSPORT", "OTHER"]
            if expense_type.upper() not in valid_types:
                return JsonResponse({
                    "status": "error",
                    "message": f"Invalid expense_type. Use: {', '.join(valid_types)}"
                }, status=400)
            
            # Validate amount
            try:
                amount = float(amount)
                if amount <= 0:
                    return JsonResponse({
                        "status": "error",
                        "message": "Amount must be positive"
                    }, status=400)
            except:
                return JsonResponse({
                    "status": "error",
                    "message": "Invalid amount"
                }, status=400)
            
            expense_id = generate_expense_id()
            
            expense_data = {
                "expense_id": expense_id,
                "emp_id": emp_id,
                "emp_name": emp.get("name"),
                "emp_role": emp.get("role", "EMPLOYEE"),
                "travel_id": travel_id,
                "expense_type": expense_type.upper(),
                "category": category,
                "amount": amount,
                "expense_date": expense_date,
                "description": description,
                "receipt": receipt if receipt else None,
                "status": "pending",
                "approved_by": None,
                "approved_by_role": None,
                "approved_date": None,
                "rejection_reason": "",
                "reimbursement_status": "pending",
                "reimbursement_date": None,
                "payment_reference": "",
                "created_date": datetime.utcnow(),
                "modified_date": datetime.utcnow(),
                "deleted_yn": 0
            }
            
            expense_collection.insert_one(expense_data)
            
            return JsonResponse({
                "status": "success",
                "message": "Expense submitted successfully",
                "expense_id": expense_id
            }, status=201)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def get(self, request):
        """List all expenses"""
        try:
            # Get query parameters
            status_filter = request.GET.get("status")
            emp_id = request.GET.get("emp_id")
            travel_id = request.GET.get("travel_id")
            
            query = {"deleted_yn": 0}
            
            if status_filter:
                query["status"] = status_filter.lower()
            
            if emp_id:
                query["emp_id"] = emp_id
            
            if travel_id:
                query["travel_id"] = travel_id
            
            expenses = list(expense_collection.find(query, {"_id": 0, "receipt.file_data": 0}).sort("created_date", -1))
            
            # Convert datetime to string
            for expense in expenses:
                if expense.get("created_date"):
                    expense["created_date"] = expense["created_date"].isoformat()
                if expense.get("modified_date"):
                    expense["modified_date"] = expense["modified_date"].isoformat()
                if expense.get("approved_date"):
                    expense["approved_date"] = expense["approved_date"].isoformat()
                if expense.get("reimbursement_date"):
                    expense["reimbursement_date"] = expense["reimbursement_date"].isoformat()
            
            return JsonResponse({
                "status": "success",
                "total": len(expenses),
                "expenses": expenses
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ExpenseDetail(APIView):
    """Get, update, or cancel specific expense"""
    
    def get(self, request, expense_id):
        """Get expense details"""
        try:
            expense = expense_collection.find_one({"expense_id": expense_id, "deleted_yn": 0}, {"_id": 0, "receipt.file_data": 0})
            
            if not expense:
                return JsonResponse({
                    "status": "error",
                    "message": "Expense not found"
                }, status=404)
            
            # Convert datetime
            if expense.get("created_date"):
                expense["created_date"] = expense["created_date"].isoformat()
            if expense.get("modified_date"):
                expense["modified_date"] = expense["modified_date"].isoformat()
            if expense.get("approved_date"):
                expense["approved_date"] = expense["approved_date"].isoformat()
            if expense.get("reimbursement_date"):
                expense["reimbursement_date"] = expense["reimbursement_date"].isoformat()
            
            return JsonResponse({
                "status": "success",
                "expense": expense
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def put(self, request, expense_id):
        """Update expense (before approval)"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            expense = expense_collection.find_one({"expense_id": expense_id, "deleted_yn": 0})
            if not expense:
                return JsonResponse({
                    "status": "error",
                    "message": "Expense not found"
                }, status=404)
            
            if expense["status"] != "pending":
                return JsonResponse({
                    "status": "error",
                    "message": f"Cannot update {expense['status']} expense"
                }, status=400)
            
            update_fields = {}
            if "category" in data:
                update_fields["category"] = data["category"]
            if "amount" in data:
                update_fields["amount"] = float(data["amount"])
            if "expense_date" in data:
                update_fields["expense_date"] = data["expense_date"]
            if "description" in data:
                update_fields["description"] = data["description"]
            if "receipt" in data:
                update_fields["receipt"] = data["receipt"]
            
            update_fields["modified_date"] = datetime.utcnow()
            
            expense_collection.update_one(
                {"expense_id": expense_id},
                {"$set": update_fields}
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Expense updated successfully"
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def delete(self, request, expense_id):
        """Cancel expense (soft delete)"""
        try:
            expense = expense_collection.find_one({"expense_id": expense_id, "deleted_yn": 0})
            if not expense:
                return JsonResponse({
                    "status": "error",
                    "message": "Expense not found"
                }, status=404)
            
            expense_collection.update_one(
                {"expense_id": expense_id},
                {"$set": {"deleted_yn": 1, "modified_date": datetime.utcnow()}}
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Expense cancelled successfully"
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ExpenseReceipt(APIView):
    """Download expense receipt"""
    
    def get(self, request, expense_id):
        """Get receipt (base64)"""
        try:
            expense = expense_collection.find_one({"expense_id": expense_id, "deleted_yn": 0}, {"_id": 0, "receipt": 1})
            
            if not expense:
                return JsonResponse({
                    "status": "error",
                    "message": "Expense not found"
                }, status=404)
            
            receipt = expense.get("receipt")
            if not receipt:
                return JsonResponse({
                    "status": "error",
                    "message": "No receipt attached"
                }, status=404)
            
            return JsonResponse({
                "status": "success",
                "receipt": receipt
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ExpenseApproval(APIView):
    """Approve or reject expense"""
    
    def post(self, request, expense_id):
        """Approve/reject expense"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            action = data.get("action")  # approve or reject
            approver_id = data.get("approver_id")
            rejection_reason = data.get("rejection_reason", "")
            
            if not action or not approver_id:
                return JsonResponse({
                    "status": "error",
                    "message": "action and approver_id are required"
                }, status=400)
            
            if action not in ["approve", "reject"]:
                return JsonResponse({
                    "status": "error",
                    "message": "Invalid action. Use 'approve' or 'reject'"
                }, status=400)
            
            # Find expense
            expense = expense_collection.find_one({"expense_id": expense_id, "deleted_yn": 0})
            if not expense:
                return JsonResponse({
                    "status": "error",
                    "message": "Expense not found"
                }, status=404)
            
            if expense["status"] != "pending":
                return JsonResponse({
                    "status": "error",
                    "message": f"Expense already {expense['status']}"
                }, status=400)
            
            # Verify approver exists
            approver = employee_collection.find_one({"emp_id": approver_id, "deleted_yn": 0})
            if not approver:
                return JsonResponse({
                    "status": "error",
                    "message": "Approver not found"
                }, status=404)
            
            approver_role = approver.get("role", "EMPLOYEE").upper()
            
            # Only Manager can approve expenses
            if approver_role != "MANAGER":
                return JsonResponse({
                    "status": "error",
                    "message": "Only Manager can approve expenses"
                }, status=403)
            
            # Update expense status
            new_status = "approved" if action == "approve" else "rejected"
            
            expense_collection.update_one(
                {"expense_id": expense_id},
                {
                    "$set": {
                        "status": new_status,
                        "approved_by": approver_id,
                        "approved_by_role": approver_role,
                        "approved_date": datetime.utcnow(),
                        "rejection_reason": rejection_reason if action == "reject" else "",
                        "modified_date": datetime.utcnow()
                    }
                }
            )
            
            return JsonResponse({
                "status": "success",
                "message": f"Expense {new_status} successfully",
                "expense_id": expense_id,
                "new_status": new_status
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ExpenseReimbursement(APIView):
    """Process reimbursement (HR only)"""
    
    def post(self, request, expense_id):
        """Mark expense as reimbursed"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            hr_id = data.get("hr_id")
            payment_reference = data.get("payment_reference", "")
            
            if not hr_id:
                return JsonResponse({
                    "status": "error",
                    "message": "hr_id is required"
                }, status=400)
            
            # Find expense
            expense = expense_collection.find_one({"expense_id": expense_id, "deleted_yn": 0})
            if not expense:
                return JsonResponse({
                    "status": "error",
                    "message": "Expense not found"
                }, status=404)
            
            if expense["status"] != "approved":
                return JsonResponse({
                    "status": "error",
                    "message": "Only approved expenses can be reimbursed"
                }, status=400)
            
            if expense["reimbursement_status"] == "paid":
                return JsonResponse({
                    "status": "error",
                    "message": "Expense already reimbursed"
                }, status=400)
            
            # Verify HR exists
            hr = employee_collection.find_one({"emp_id": hr_id, "deleted_yn": 0})
            if not hr:
                return JsonResponse({
                    "status": "error",
                    "message": "HR not found"
                }, status=404)
            
            hr_role = hr.get("role", "EMPLOYEE").upper()
            
            # Only HR can process reimbursement
            if hr_role != "HR":
                return JsonResponse({
                    "status": "error",
                    "message": "Only HR can process reimbursement"
                }, status=403)
            
            # Update reimbursement status
            expense_collection.update_one(
                {"expense_id": expense_id},
                {
                    "$set": {
                        "reimbursement_status": "paid",
                        "reimbursement_date": datetime.utcnow(),
                        "payment_reference": payment_reference,
                        "modified_date": datetime.utcnow()
                    }
                }
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Reimbursement processed successfully",
                "expense_id": expense_id,
                "payment_reference": payment_reference
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ReimbursementSummary(APIView):
    """Get reimbursement summary for employee"""
    
    def get(self, request, emp_id):
        """Get summary of expenses"""
        try:
            # Verify employee exists
            emp = employee_collection.find_one({"emp_id": emp_id, "deleted_yn": 0})
            if not emp:
                return JsonResponse({
                    "status": "error",
                    "message": "Employee not found"
                }, status=404)
            
            # Get all expenses for employee
            expenses = list(expense_collection.find({"emp_id": emp_id, "deleted_yn": 0}))
            
            # Calculate totals
            total_pending = sum(e["amount"] for e in expenses if e["status"] == "pending")
            total_approved = sum(e["amount"] for e in expenses if e["status"] == "approved" and e["reimbursement_status"] != "paid")
            total_reimbursed = sum(e["amount"] for e in expenses if e["reimbursement_status"] == "paid")
            total_rejected = sum(e["amount"] for e in expenses if e["status"] == "rejected")
            
            # Count expenses
            count_pending = len([e for e in expenses if e["status"] == "pending"])
            count_approved = len([e for e in expenses if e["status"] == "approved" and e["reimbursement_status"] != "paid"])
            count_reimbursed = len([e for e in expenses if e["reimbursement_status"] == "paid"])
            count_rejected = len([e for e in expenses if e["status"] == "rejected"])
            
            return JsonResponse({
                "status": "success",
                "emp_id": emp_id,
                "emp_name": emp.get("name"),
                "summary": {
                    "pending": {
                        "count": count_pending,
                        "amount": total_pending
                    },
                    "approved": {
                        "count": count_approved,
                        "amount": total_approved
                    },
                    "reimbursed": {
                        "count": count_reimbursed,
                        "amount": total_reimbursed
                    },
                    "rejected": {
                        "count": count_rejected,
                        "amount": total_rejected
                    },
                    "total_expenses": len(expenses),
                    "outstanding_balance": total_approved
                }
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
