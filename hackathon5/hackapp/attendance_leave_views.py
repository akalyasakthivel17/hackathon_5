from rest_framework.views import APIView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import json

# MongoDB Connection
client = MongoClient("mongodb+srv://akalyabharath20_db_user:LVyhweJauTGaO0pp@cluster0.2ss7wcx.mongodb.net/")
db = client["test"]
employee_collection = db["employees"]
attendance_collection = db["attendance"]
leave_collection = db["leaves"]
leave_balance_collection = db["leave_balance"]


# --------------------------
# ATTENDANCE APIs
# --------------------------
@method_decorator(csrf_exempt, name='dispatch')
class AttendanceCheckInOut(APIView):
    """Check-in and Check-out API"""
    
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
            emp_id = data.get("emp_id")
            action = data.get("action")  # "check-in" or "check-out"
            
            if not emp_id or not action:
                return JsonResponse({
                    "status": "error",
                    "message": "emp_id and action required"
                }, status=400)
            
            # Verify employee exists
            emp = employee_collection.find_one({"emp_id": emp_id, "deleted_yn": 0})
            if not emp:
                return JsonResponse({
                    "status": "error",
                    "message": "Employee not found"
                }, status=404)
            
            now = datetime.utcnow()
            today = now.date()
            
            if action == "check-in":
                # Check if already checked in today
                existing = attendance_collection.find_one({
                    "emp_id": emp_id,
                    "date": str(today),
                    "check_out": None
                })
                
                if existing:
                    return JsonResponse({
                        "status": "error",
                        "message": "Already checked in today"
                    }, status=400)
                
                # Create new attendance record
                attendance_record = {
                    "emp_id": emp_id,
                    "date": str(today),
                    "check_in": now,
                    "check_out": None,
                    "working_hours": 0,
                    "created_date": now
                }
                
                attendance_collection.insert_one(attendance_record)
                
                return JsonResponse({
                    "status": "success",
                    "message": "Checked in successfully",
                    "check_in_time": now.isoformat()
                }, status=201)
            
            elif action == "check-out":
                # Find today's check-in record
                record = attendance_collection.find_one({
                    "emp_id": emp_id,
                    "date": str(today),
                    "check_out": None
                })
                
                if not record:
                    return JsonResponse({
                        "status": "error",
                        "message": "No active check-in found for today"
                    }, status=400)
                
                # Calculate working hours
                check_in_time = record["check_in"]
                working_hours = (now - check_in_time).total_seconds() / 3600
                
                # Update record with check-out
                attendance_collection.update_one(
                    {"_id": record["_id"]},
                    {
                        "$set": {
                            "check_out": now,
                            "working_hours": round(working_hours, 2)
                        }
                    }
                )
                
                return JsonResponse({
                    "status": "success",
                    "message": "Checked out successfully",
                    "check_out_time": now.isoformat(),
                    "working_hours": round(working_hours, 2)
                }, status=200)
            
            else:
                return JsonResponse({
                    "status": "error",
                    "message": "Invalid action. Use 'check-in' or 'check-out'"
                }, status=400)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AttendanceHistory(APIView):
    """Get attendance history for an employee"""
    
    def get(self, request, emp_id):
        try:
            # Verify employee exists
            emp = employee_collection.find_one({"emp_id": emp_id, "deleted_yn": 0})
            if not emp:
                return JsonResponse({
                    "status": "error",
                    "message": "Employee not found"
                }, status=404)
            
            # Get query parameters
            month = request.GET.get("month")  # Format: YYYY-MM
            
            query = {"emp_id": emp_id}
            
            if month:
                # Filter by month
                query["date"] = {"$regex": f"^{month}"}
            
            # Fetch attendance records
            records = list(attendance_collection.find(query, {"_id": 0}).sort("date", -1))
            
            # Convert datetime to string for JSON serialization
            for record in records:
                if record.get("check_in"):
                    record["check_in"] = record["check_in"].isoformat()
                if record.get("check_out"):
                    record["check_out"] = record["check_out"].isoformat()
            
            # Calculate total working hours
            total_hours = sum(r.get("working_hours", 0) for r in records)
            
            return JsonResponse({
                "status": "success",
                "emp_id": emp_id,
                "total_records": len(records),
                "total_working_hours": round(total_hours, 2),
                "attendance": records
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class MonthlyAttendanceReport(APIView):
    """Generate monthly attendance report"""
    
    def get(self, request, emp_id):
        try:
            month = request.GET.get("month")  # Format: YYYY-MM
            
            if not month:
                return JsonResponse({
                    "status": "error",
                    "message": "month parameter required (format: YYYY-MM)"
                }, status=400)
            
            # Verify employee exists
            emp = employee_collection.find_one({"emp_id": emp_id, "deleted_yn": 0})
            if not emp:
                return JsonResponse({
                    "status": "error",
                    "message": "Employee not found"
                }, status=404)
            
            # Fetch attendance for the month
            records = list(attendance_collection.find({
                "emp_id": emp_id,
                "date": {"$regex": f"^{month}"}
            }, {"_id": 0}).sort("date", 1))
            
            # Convert datetime to string
            for record in records:
                if record.get("check_in"):
                    record["check_in"] = record["check_in"].isoformat()
                if record.get("check_out"):
                    record["check_out"] = record["check_out"].isoformat()
            
            total_days = len(records)
            total_hours = sum(r.get("working_hours", 0) for r in records)
            avg_hours = round(total_hours / total_days, 2) if total_days > 0 else 0
            
            return JsonResponse({
                "status": "success",
                "emp_id": emp_id,
                "name": emp.get("name"),
                "month": month,
                "total_days_worked": total_days,
                "total_working_hours": round(total_hours, 2),
                "average_hours_per_day": avg_hours,
                "attendance_records": records
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


# --------------------------
# LEAVE MANAGEMENT APIs
# --------------------------
@method_decorator(csrf_exempt, name='dispatch')
class LeaveBalance(APIView):
    """Get or initialize leave balance for an employee"""
    
    def get(self, request, emp_id):
        try:
            # Verify employee exists
            emp = employee_collection.find_one({"emp_id": emp_id, "deleted_yn": 0})
            if not emp:
                return JsonResponse({
                    "status": "error",
                    "message": "Employee not found"
                }, status=404)
            
            # Get or create leave balance
            balance = leave_balance_collection.find_one({"emp_id": emp_id})
            
            if not balance:
                # Initialize default balance
                balance = {
                    "emp_id": emp_id,
                    "casual": 12,
                    "sick": 12,
                    "vacation": 15,
                    "created_date": datetime.utcnow(),
                    "updated_date": datetime.utcnow()
                }
                leave_balance_collection.insert_one(balance)
            
            return JsonResponse({
                "status": "success",
                "emp_id": emp_id,
                "leave_balance": {
                    "casual": balance.get("casual", 12),
                    "sick": balance.get("sick", 12),
                    "vacation": balance.get("vacation", 15)
                }
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class LeaveApplication(APIView):
    """Apply for leave"""
    
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
            emp_id = data.get("emp_id")
            leave_type = data.get("leave_type")  # casual, sick, vacation
            start_date = data.get("start_date")  # YYYY-MM-DD
            end_date = data.get("end_date")  # YYYY-MM-DD
            reason = data.get("reason", "")
            
            if not all([emp_id, leave_type, start_date, end_date]):
                return JsonResponse({
                    "status": "error",
                    "message": "emp_id, leave_type, start_date, and end_date are required"
                }, status=400)
            
            # Validate leave type
            if leave_type not in ["casual", "sick", "vacation"]:
                return JsonResponse({
                    "status": "error",
                    "message": "Invalid leave_type. Use: casual, sick, or vacation"
                }, status=400)
            
            # Verify employee exists
            emp = employee_collection.find_one({"emp_id": emp_id, "deleted_yn": 0})
            if not emp:
                return JsonResponse({
                    "status": "error",
                    "message": "Employee not found"
                }, status=404)
            
            # Calculate number of days
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            days_requested = (end - start).days + 1
            
            if days_requested <= 0:
                return JsonResponse({
                    "status": "error",
                    "message": "Invalid date range"
                }, status=400)
            
            # Check leave balance
            balance = leave_balance_collection.find_one({"emp_id": emp_id})
            if not balance:
                # Initialize default balance
                balance = {
                    "emp_id": emp_id,
                    "casual": 12,
                    "sick": 12,
                    "vacation": 15
                }
                leave_balance_collection.insert_one(balance)
            
            available = balance.get(leave_type, 0)
            
            if available < days_requested:
                return JsonResponse({
                    "status": "error",
                    "message": f"Insufficient {leave_type} leave balance. Available: {available}, Requested: {days_requested}"
                }, status=400)
            
            # Create leave application
            leave_app = {
                "emp_id": emp_id,
                "leave_type": leave_type,
                "start_date": start_date,
                "end_date": end_date,
                "days": days_requested,
                "reason": reason,
                "status": "pending",  # pending, approved, rejected
                "applied_date": datetime.utcnow(),
                "approved_by": None,
                "approved_date": None
            }
            
            result = leave_collection.insert_one(leave_app)
            
            return JsonResponse({
                "status": "success",
                "message": "Leave application submitted successfully",
                "leave_id": str(result.inserted_id),
                "days_requested": days_requested,
                "current_status": "pending"
            }, status=201)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def get(self, request, emp_id):
        """Get leave applications for an employee"""
        try:
            # Verify employee exists
            emp = employee_collection.find_one({"emp_id": emp_id, "deleted_yn": 0})
            if not emp:
                return JsonResponse({
                    "status": "error",
                    "message": "Employee not found"
                }, status=404)
            
            # Get all leave applications
            leaves = list(leave_collection.find({"emp_id": emp_id}, {"_id": 0}).sort("applied_date", -1))
            
            # Convert datetime to string
            for leave in leaves:
                if leave.get("applied_date"):
                    leave["applied_date"] = leave["applied_date"].isoformat()
                if leave.get("approved_date"):
                    leave["approved_date"] = leave["approved_date"].isoformat()
            
            return JsonResponse({
                "status": "success",
                "emp_id": emp_id,
                "total_applications": len(leaves),
                "leave_applications": leaves
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class LeaveApproval(APIView):
    """Manager approval workflow for leave"""
    
    def post(self, request, leave_id):
        try:
            data = json.loads(request.body.decode('utf-8'))
            action = data.get("action")  # approve or reject
            manager_id = data.get("manager_id")
            
            if not action or not manager_id:
                return JsonResponse({
                    "status": "error",
                    "message": "action and manager_id are required"
                }, status=400)
            
            if action not in ["approve", "reject"]:
                return JsonResponse({
                    "status": "error",
                    "message": "Invalid action. Use 'approve' or 'reject'"
                }, status=400)
            
            # Find leave application
            leave_app = leave_collection.find_one({"_id": ObjectId(leave_id)})
            
            if not leave_app:
                return JsonResponse({
                    "status": "error",
                    "message": "Leave application not found"
                }, status=404)
            
            if leave_app["status"] != "pending":
                return JsonResponse({
                    "status": "error",
                    "message": f"Leave already {leave_app['status']}"
                }, status=400)
            
            # Update leave status
            new_status = "approved" if action == "approve" else "rejected"
            
            leave_collection.update_one(
                {"_id": ObjectId(leave_id)},
                {
                    "$set": {
                        "status": new_status,
                        "approved_by": manager_id,
                        "approved_date": datetime.utcnow()
                    }
                }
            )
            
            # If approved, deduct from leave balance
            if action == "approve":
                leave_balance_collection.update_one(
                    {"emp_id": leave_app["emp_id"]},
                    {
                        "$inc": {leave_app["leave_type"]: -leave_app["days"]},
                        "$set": {"updated_date": datetime.utcnow()}
                    }
                )
            
            return JsonResponse({
                "status": "success",
                "message": f"Leave {new_status} successfully",
                "leave_id": leave_id,
                "new_status": new_status
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ManagerLeaveRequests(APIView):
    """Get all pending leave requests for manager dashboard"""
    
    def get(self, request):
        try:
            status_filter = request.GET.get("status", "pending")
            
            # Get all leave applications with the specified status
            leaves = list(leave_collection.find({"status": status_filter}, {"_id": 1}).sort("applied_date", -1))
            
            # Enrich with employee details
            result = []
            for leave in leaves:
                leave_id = str(leave["_id"])
                leave_data = leave_collection.find_one({"_id": leave["_id"]})
                
                emp = employee_collection.find_one({"emp_id": leave_data["emp_id"]}, {"_id": 0, "name": 1, "email": 1})
                
                # Convert datetime to string
                if leave_data.get("applied_date"):
                    leave_data["applied_date"] = leave_data["applied_date"].isoformat()
                if leave_data.get("approved_date"):
                    leave_data["approved_date"] = leave_data["approved_date"].isoformat()
                
                result.append({
                    "leave_id": leave_id,
                    "emp_id": leave_data["emp_id"],
                    "emp_name": emp.get("name") if emp else "Unknown",
                    "emp_email": emp.get("email") if emp else "Unknown",
                    "leave_type": leave_data["leave_type"],
                    "start_date": leave_data["start_date"],
                    "end_date": leave_data["end_date"],
                    "days": leave_data["days"],
                    "reason": leave_data.get("reason", ""),
                    "status": leave_data["status"],
                    "applied_date": leave_data.get("applied_date")
                })
            
            return JsonResponse({
                "status": "success",
                "total_requests": len(result),
                "leave_requests": result
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


# --------------------------
# MANAGER ATTENDANCE DASHBOARD
# --------------------------
@method_decorator(csrf_exempt, name='dispatch')
class ManagerAttendanceDashboard(APIView):
    """Manager dashboard - Overview of all employees' attendance"""
    
    def get(self, request):
        try:
            today = datetime.utcnow().date()
            today_str = str(today)
            
            # Get all active employees
            all_employees = list(employee_collection.find({"deleted_yn": 0}))
            
            total_employees = len(all_employees)
            present_today = 0
            checked_out = 0
            
            employee_attendance_list = []
            
            for emp in all_employees:
                emp_id = emp.get("emp_id")
                emp_name = emp.get("name", "Unknown")
                emp_department = emp.get("department", "N/A")
                emp_role = emp.get("role", "EMPLOYEE")
                
                # Get today's attendance
                attendance = attendance_collection.find_one({
                    "emp_id": emp_id,
                    "date": today_str
                })
                
                if attendance:
                    present_today += 1
                    check_in = attendance.get("check_in")
                    check_out = attendance.get("check_out")
                    working_hours = attendance.get("working_hours", 0)
                    
                    if check_out:
                        checked_out += 1
                        today_status = "checked_out"
                    else:
                        today_status = "present"
                    
                    # Format times
                    check_in_time = check_in.strftime("%H:%M:%S") if check_in else None
                    check_out_time = check_out.strftime("%H:%M:%S") if check_out else None
                else:
                    today_status = "absent"
                    check_in_time = None
                    check_out_time = None
                    working_hours = 0
                
                # Get this week's attendance count
                week_start = today - timedelta(days=today.weekday())
                week_records = attendance_collection.count_documents({
                    "emp_id": emp_id,
                    "date": {"$gte": str(week_start), "$lte": today_str}
                })
                
                employee_attendance_list.append({
                    "emp_id": emp_id,
                    "name": emp_name,
                    "department": emp_department,
                    "role": emp_role,
                    "today_status": today_status,
                    "check_in": check_in_time,
                    "check_out": check_out_time,
                    "hours": round(working_hours, 2),
                    "this_week": f"{week_records}/{today.weekday() + 1} days"
                })
            
            # Calculate attendance rate
            attendance_rate = round((present_today / total_employees * 100), 2) if total_employees > 0 else 0
            
            return JsonResponse({
                "status": "success",
                "dashboard": {
                    "overview": {
                        "total_employees": total_employees,
                        "present_today": present_today,
                        "checked_out": checked_out,
                        "attendance_rate": attendance_rate
                    },
                    "employee_attendance": employee_attendance_list
                }
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
