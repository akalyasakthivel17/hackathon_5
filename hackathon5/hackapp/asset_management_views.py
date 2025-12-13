from rest_framework.views import APIView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from pymongo import MongoClient
from datetime import datetime
import json

# MongoDB Connection
client = MongoClient("mongodb+srv://akalyabharath20_db_user:LVyhweJauTGaO0pp@cluster0.2ss7wcx.mongodb.net/")
db = client["test"]
employee_collection = db["employees"]
assets_collection = db["assets"]
asset_assignments_collection = db["asset_assignments"]


# --------------------------
# HELPER FUNCTIONS
# --------------------------
def generate_asset_id():
    """Generate sequential asset ID (AST001, AST002, ...)"""
    last_asset = assets_collection.find_one(
        {"asset_id": {"$exists": True}},
        sort=[("asset_id", -1)]
    )
    if not last_asset:
        return "AST001"
    try:
        num = int(last_asset["asset_id"].replace("AST", "")) + 1
        return f"AST{num:03d}"
    except:
        count = assets_collection.count_documents({"asset_id": {"$exists": True}})
        return f"AST{count+1:03d}"


def generate_assignment_id():
    """Generate sequential assignment ID (ASGN001, ASGN002, ...)"""
    last_assignment = asset_assignments_collection.find_one(
        {"assignment_id": {"$exists": True}},
        sort=[("assignment_id", -1)]
    )
    if not last_assignment:
        return "ASGN001"
    try:
        num = int(last_assignment["assignment_id"].replace("ASGN", "")) + 1
        return f"ASGN{num:03d}"
    except:
        count = asset_assignments_collection.count_documents({"assignment_id": {"$exists": True}})
        return f"ASGN{count+1:03d}"


# --------------------------
# API 1: ASSET MANAGEMENT (CRUD)
# --------------------------
@method_decorator(csrf_exempt, name='dispatch')
class AssetManagementAPI(APIView):
    """Manage company assets - Create, Read, Update, Delete"""
    
    def post(self, request):
        """Add new asset"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            asset_name = data.get("asset_name")
            asset_type = data.get("asset_type", "OTHER")  # LAPTOP, DESKTOP, MONITOR, PHONE, OTHER
            serial_number = data.get("serial_number", "")
            purchase_date = data.get("purchase_date")
            purchase_cost = data.get("purchase_cost", 0)
            condition = data.get("condition", "good")  # good, fair, poor
            
            if not asset_name:
                return JsonResponse({
                    "status": "error",
                    "message": "asset_name is required"
                }, status=400)
            
            # Validate asset_type
            valid_types = ["LAPTOP", "DESKTOP", "MONITOR", "PHONE", "KEYBOARD", "MOUSE", "OTHER"]
            if asset_type.upper() not in valid_types:
                return JsonResponse({
                    "status": "error",
                    "message": f"Invalid asset_type. Use: {', '.join(valid_types)}"
                }, status=400)
            
            asset_id = generate_asset_id()
            
            asset_data = {
                "asset_id": asset_id,
                "asset_name": asset_name,
                "asset_type": asset_type.upper(),
                "serial_number": serial_number,
                "purchase_date": purchase_date,
                "purchase_cost": float(purchase_cost),
                "status": "available",  # available, assigned, maintenance, retired
                "condition": condition.lower(),
                "assigned_to": None,
                "assigned_to_name": None,
                "created_date": datetime.utcnow(),
                "modified_date": datetime.utcnow(),
                "deleted_yn": 0
            }
            
            assets_collection.insert_one(asset_data)
            
            return JsonResponse({
                "status": "success",
                "message": "Asset added successfully",
                "asset_id": asset_id
            }, status=201)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def get(self, request):
        """List all assets with filters"""
        try:
            # Get query parameters
            status_filter = request.GET.get("status")  # available, assigned, maintenance, retired
            asset_type = request.GET.get("type")  # LAPTOP, DESKTOP, etc.
            emp_id = request.GET.get("emp_id")  # Filter by assigned employee
            
            query = {"deleted_yn": 0}
            
            if status_filter:
                query["status"] = status_filter.lower()
            
            if asset_type:
                query["asset_type"] = asset_type.upper()
            
            if emp_id:
                query["assigned_to"] = emp_id
            
            assets = list(assets_collection.find(query, {"_id": 0}).sort("created_date", -1))
            
            # Convert datetime to string
            for asset in assets:
                if asset.get("created_date"):
                    asset["created_date"] = asset["created_date"].isoformat()
                if asset.get("modified_date"):
                    asset["modified_date"] = asset["modified_date"].isoformat()
            
            return JsonResponse({
                "status": "success",
                "total": len(assets),
                "assets": assets
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def put(self, request):
        """Update asset details"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            asset_id = data.get("asset_id")
            
            if not asset_id:
                return JsonResponse({
                    "status": "error",
                    "message": "asset_id is required"
                }, status=400)
            
            asset = assets_collection.find_one({"asset_id": asset_id, "deleted_yn": 0})
            if not asset:
                return JsonResponse({
                    "status": "error",
                    "message": "Asset not found"
                }, status=404)
            
            update_fields = {}
            if "asset_name" in data:
                update_fields["asset_name"] = data["asset_name"]
            if "asset_type" in data:
                update_fields["asset_type"] = data["asset_type"].upper()
            if "serial_number" in data:
                update_fields["serial_number"] = data["serial_number"]
            if "purchase_cost" in data:
                update_fields["purchase_cost"] = float(data["purchase_cost"])
            if "condition" in data:
                update_fields["condition"] = data["condition"].lower()
            if "status" in data:
                update_fields["status"] = data["status"].lower()
            
            update_fields["modified_date"] = datetime.utcnow()
            
            assets_collection.update_one(
                {"asset_id": asset_id},
                {"$set": update_fields}
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Asset updated successfully"
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def delete(self, request):
        """Soft delete asset"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            asset_id = data.get("asset_id")
            
            if not asset_id:
                return JsonResponse({
                    "status": "error",
                    "message": "asset_id is required"
                }, status=400)
            
            asset = assets_collection.find_one({"asset_id": asset_id, "deleted_yn": 0})
            if not asset:
                return JsonResponse({
                    "status": "error",
                    "message": "Asset not found"
                }, status=404)
            
            # Check if asset is assigned
            if asset.get("status") == "assigned":
                return JsonResponse({
                    "status": "error",
                    "message": "Cannot delete assigned asset. Return it first."
                }, status=400)
            
            assets_collection.update_one(
                {"asset_id": asset_id},
                {"$set": {"deleted_yn": 1, "modified_date": datetime.utcnow()}}
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Asset deleted successfully"
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


# --------------------------
# API 2: ASSET ASSIGNMENT & RETURN
# --------------------------
@method_decorator(csrf_exempt, name='dispatch')
class AssetAssignmentAPI(APIView):
    """Assign assets to employees and handle returns"""
    
    def post(self, request):
        """Assign asset to employee"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            asset_id = data.get("asset_id")
            emp_id = data.get("emp_id")
            notes = data.get("notes", "")
            
            if not all([asset_id, emp_id]):
                return JsonResponse({
                    "status": "error",
                    "message": "asset_id and emp_id are required"
                }, status=400)
            
            # Verify asset exists and is available
            asset = assets_collection.find_one({"asset_id": asset_id, "deleted_yn": 0})
            if not asset:
                return JsonResponse({
                    "status": "error",
                    "message": "Asset not found"
                }, status=404)
            
            if asset.get("status") != "available":
                return JsonResponse({
                    "status": "error",
                    "message": f"Asset is {asset.get('status')}, not available"
                }, status=400)
            
            # Verify employee exists
            emp = employee_collection.find_one({"emp_id": emp_id, "deleted_yn": 0})
            if not emp:
                return JsonResponse({
                    "status": "error",
                    "message": "Employee not found"
                }, status=404)
            
            assignment_id = generate_assignment_id()
            
            # Create assignment record
            assignment_data = {
                "assignment_id": assignment_id,
                "asset_id": asset_id,
                "asset_name": asset.get("asset_name"),
                "emp_id": emp_id,
                "emp_name": emp.get("name"),
                "assigned_date": datetime.utcnow(),
                "return_date": None,
                "status": "active",  # active, returned
                "notes": notes,
                "created_date": datetime.utcnow(),
                "deleted_yn": 0
            }
            
            asset_assignments_collection.insert_one(assignment_data)
            
            # Update asset status
            assets_collection.update_one(
                {"asset_id": asset_id},
                {"$set": {
                    "status": "assigned",
                    "assigned_to": emp_id,
                    "assigned_to_name": emp.get("name"),
                    "modified_date": datetime.utcnow()
                }}
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Asset assigned successfully",
                "assignment_id": assignment_id
            }, status=201)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def put(self, request):
        """Return asset"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            assignment_id = data.get("assignment_id")
            condition = data.get("condition", "good")  # Condition on return
            
            if not assignment_id:
                return JsonResponse({
                    "status": "error",
                    "message": "assignment_id is required"
                }, status=400)
            
            # Find active assignment
            assignment = asset_assignments_collection.find_one({
                "assignment_id": assignment_id,
                "status": "active",
                "deleted_yn": 0
            })
            
            if not assignment:
                return JsonResponse({
                    "status": "error",
                    "message": "Active assignment not found"
                }, status=404)
            
            asset_id = assignment.get("asset_id")
            
            # Update assignment record
            asset_assignments_collection.update_one(
                {"assignment_id": assignment_id},
                {"$set": {
                    "status": "returned",
                    "return_date": datetime.utcnow()
                }}
            )
            
            # Update asset status
            assets_collection.update_one(
                {"asset_id": asset_id},
                {"$set": {
                    "status": "available",
                    "assigned_to": None,
                    "assigned_to_name": None,
                    "condition": condition.lower(),
                    "modified_date": datetime.utcnow()
                }}
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Asset returned successfully"
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def get(self, request):
        """Get assignment history"""
        try:
            # Get query parameters
            emp_id = request.GET.get("emp_id")
            asset_id = request.GET.get("asset_id")
            status_filter = request.GET.get("status")  # active, returned
            
            query = {"deleted_yn": 0}
            
            if emp_id:
                query["emp_id"] = emp_id
            
            if asset_id:
                query["asset_id"] = asset_id
            
            if status_filter:
                query["status"] = status_filter.lower()
            
            assignments = list(asset_assignments_collection.find(query, {"_id": 0}).sort("assigned_date", -1))
            
            # Convert datetime to string
            for assignment in assignments:
                if assignment.get("assigned_date"):
                    assignment["assigned_date"] = assignment["assigned_date"].isoformat()
                if assignment.get("return_date"):
                    assignment["return_date"] = assignment["return_date"].isoformat()
                if assignment.get("created_date"):
                    assignment["created_date"] = assignment["created_date"].isoformat()
            
            return JsonResponse({
                "status": "success",
                "total": len(assignments),
                "assignments": assignments
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


# --------------------------
# API 3: ASSET DASHBOARD (COMBINED)
# --------------------------
@method_decorator(csrf_exempt, name='dispatch')
class AssetDashboardAPI(APIView):
    """Combined dashboard - Asset statistics and inventory overview"""
    
    def get(self, request):
        try:
            # Get all active assets
            all_assets = list(assets_collection.find({"deleted_yn": 0}))
            
            # Calculate statistics
            total_assets = len(all_assets)
            available_count = len([a for a in all_assets if a.get("status") == "available"])
            assigned_count = len([a for a in all_assets if a.get("status") == "assigned"])
            maintenance_count = len([a for a in all_assets if a.get("status") == "maintenance"])
            retired_count = len([a for a in all_assets if a.get("status") == "retired"])
            
            # Assets by type
            assets_by_type = {}
            for asset in all_assets:
                asset_type = asset.get("asset_type", "OTHER")
                if asset_type not in assets_by_type:
                    assets_by_type[asset_type] = 0
                assets_by_type[asset_type] += 1
            
            # Recent assignments (last 5)
            recent_assignments = list(asset_assignments_collection.find(
                {"deleted_yn": 0},
                {"_id": 0}
            ).sort("assigned_date", -1).limit(5))
            
            # Convert datetime
            for assignment in recent_assignments:
                if assignment.get("assigned_date"):
                    assignment["assigned_date"] = assignment["assigned_date"].isoformat()
                if assignment.get("return_date"):
                    assignment["return_date"] = assignment["return_date"].isoformat()
            
            # Assets needing attention (poor condition or in maintenance)
            attention_needed = []
            for asset in all_assets:
                if asset.get("condition") == "poor" or asset.get("status") == "maintenance":
                    attention_needed.append({
                        "asset_id": asset.get("asset_id"),
                        "asset_name": asset.get("asset_name"),
                        "condition": asset.get("condition"),
                        "status": asset.get("status")
                    })
            
            return JsonResponse({
                "status": "success",
                "dashboard": {
                    "overview": {
                        "total_assets": total_assets,
                        "available": available_count,
                        "assigned": assigned_count,
                        "maintenance": maintenance_count,
                        "retired": retired_count
                    },
                    "assets_by_type": assets_by_type,
                    "recent_assignments": {
                        "total": len(recent_assignments),
                        "assignments": recent_assignments
                    },
                    "attention_needed": {
                        "total": len(attention_needed),
                        "assets": attention_needed
                    }
                }
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
