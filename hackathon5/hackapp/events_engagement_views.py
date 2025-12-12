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
events_collection = db["events"]
kudos_collection = db["kudos"]
announcements_collection = db["announcements"]


# --------------------------
# HELPER FUNCTIONS
# --------------------------
def generate_event_id():
    """Generate sequential event ID (EVT001, EVT002, ...)"""
    last_event = events_collection.find_one(
        {"event_id": {"$exists": True}},
        sort=[("event_id", -1)]
    )
    if not last_event:
        return "EVT001"
    try:
        num = int(last_event["event_id"].replace("EVT", "")) + 1
        return f"EVT{num:03d}"
    except:
        count = events_collection.count_documents({"event_id": {"$exists": True}})
        return f"EVT{count+1:03d}"


def generate_kudos_id():
    """Generate sequential kudos ID (KUD001, KUD002, ...)"""
    last_kudos = kudos_collection.find_one(
        {"kudos_id": {"$exists": True}},
        sort=[("kudos_id", -1)]
    )
    if not last_kudos:
        return "KUD001"
    try:
        num = int(last_kudos["kudos_id"].replace("KUD", "")) + 1
        return f"KUD{num:03d}"
    except:
        count = kudos_collection.count_documents({"kudos_id": {"$exists": True}})
        return f"KUD{count+1:03d}"


def generate_announcement_id():
    """Generate sequential announcement ID (ANN001, ANN002, ...)"""
    last_ann = announcements_collection.find_one(
        {"announcement_id": {"$exists": True}},
        sort=[("announcement_id", -1)]
    )
    if not last_ann:
        return "ANN001"
    try:
        num = int(last_ann["announcement_id"].replace("ANN", "")) + 1
        return f"ANN{num:03d}"
    except:
        count = announcements_collection.count_documents({"announcement_id": {"$exists": True}})
        return f"ANN{count+1:03d}"


def generate_comment_id():
    """Generate sequential comment ID (COM001, COM002, ...)"""
    import random
    return f"COM{random.randint(1000, 9999)}"


# --------------------------
# BIRTHDAYS APIs
# --------------------------
@method_decorator(csrf_exempt, name='dispatch')
class UpcomingBirthdays(APIView):
    """Get upcoming birthdays in next 30 days"""
    
    def get(self, request):
        try:
            today = datetime.now()
            upcoming_birthdays = []
            
            # Get all active employees
            employees = list(employee_collection.find({"deleted_yn": 0}))
            
            for emp in employees:
                dob = emp.get("dob")
                if not dob:
                    continue
                
                try:
                    # Parse DOB (format: YYYY-MM-DD)
                    birth_date = datetime.strptime(dob, "%Y-%m-%d")
                    
                    # Get this year's birthday
                    this_year_birthday = birth_date.replace(year=today.year)
                    
                    # If birthday already passed this year, check next year
                    if this_year_birthday < today:
                        this_year_birthday = birth_date.replace(year=today.year + 1)
                    
                    # Check if birthday is within next 30 days
                    days_until = (this_year_birthday - today).days
                    
                    if 0 <= days_until <= 30:
                        upcoming_birthdays.append({
                            "emp_id": emp.get("emp_id"),
                            "name": emp.get("name"),
                            "email": emp.get("email"),
                            "dob": dob,
                            "birthday_date": this_year_birthday.strftime("%Y-%m-%d"),
                            "days_until": days_until
                        })
                except:
                    continue
            
            # Sort by days_until
            upcoming_birthdays.sort(key=lambda x: x["days_until"])
            
            return JsonResponse({
                "status": "success",
                "total": len(upcoming_birthdays),
                "birthdays": upcoming_birthdays
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class TodayBirthdays(APIView):
    """Get today's birthdays"""
    
    def get(self, request):
        try:
            today = datetime.now()
            today_birthdays = []
            
            # Get all active employees
            employees = list(employee_collection.find({"deleted_yn": 0}))
            
            for emp in employees:
                dob = emp.get("dob")
                if not dob:
                    continue
                
                try:
                    # Parse DOB
                    birth_date = datetime.strptime(dob, "%Y-%m-%d")
                    
                    # Check if month and day match today
                    if birth_date.month == today.month and birth_date.day == today.day:
                        age = today.year - birth_date.year
                        today_birthdays.append({
                            "emp_id": emp.get("emp_id"),
                            "name": emp.get("name"),
                            "email": emp.get("email"),
                            "dob": dob,
                            "age": age
                        })
                except:
                    continue
            
            return JsonResponse({
                "status": "success",
                "total": len(today_birthdays),
                "birthdays": today_birthdays
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


# --------------------------
# EVENT CALENDAR APIs
# --------------------------
@method_decorator(csrf_exempt, name='dispatch')
class EventCalendar(APIView):
    """Create and list company events"""
    
    def post(self, request):
        """Create new event"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            title = data.get("title")
            description = data.get("description", "")
            event_type = data.get("event_type", "MEETING")  # MEETING, HOLIDAY, CELEBRATION
            event_date = data.get("event_date")  # YYYY-MM-DD
            start_time = data.get("start_time", "")
            end_time = data.get("end_time", "")
            location = data.get("location", "")
            created_by = data.get("created_by")
            
            if not all([title, event_date, created_by]):
                return JsonResponse({
                    "status": "error",
                    "message": "title, event_date, and created_by are required"
                }, status=400)
            
            # Verify creator exists
            creator = employee_collection.find_one({"emp_id": created_by, "deleted_yn": 0})
            if not creator:
                return JsonResponse({
                    "status": "error",
                    "message": "Creator employee not found"
                }, status=404)
            
            # Validate event type
            valid_types = ["MEETING", "HOLIDAY", "CELEBRATION"]
            if event_type.upper() not in valid_types:
                return JsonResponse({
                    "status": "error",
                    "message": f"Invalid event_type. Use: {', '.join(valid_types)}"
                }, status=400)
            
            event_id = generate_event_id()
            
            event_data = {
                "event_id": event_id,
                "title": title,
                "description": description,
                "event_type": event_type.upper(),
                "event_date": event_date,
                "start_time": start_time,
                "end_time": end_time,
                "location": location,
                "created_by": created_by,
                "created_by_name": creator.get("name"),
                "created_date": datetime.utcnow(),
                "modified_date": datetime.utcnow(),
                "deleted_yn": 0
            }
            
            events_collection.insert_one(event_data)
            
            return JsonResponse({
                "status": "success",
                "message": "Event created successfully",
                "event_id": event_id
            }, status=201)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def get(self, request):
        """List all events"""
        try:
            # Get query parameters
            month = request.GET.get("month")  # YYYY-MM
            event_type = request.GET.get("type")  # MEETING, HOLIDAY, CELEBRATION
            
            query = {"deleted_yn": 0}
            
            if month:
                query["event_date"] = {"$regex": f"^{month}"}
            
            if event_type:
                query["event_type"] = event_type.upper()
            
            events = list(events_collection.find(query, {"_id": 0}).sort("event_date", 1))
            
            # Convert datetime to string
            for event in events:
                if event.get("created_date"):
                    event["created_date"] = event["created_date"].isoformat()
                if event.get("modified_date"):
                    event["modified_date"] = event["modified_date"].isoformat()
            
            return JsonResponse({
                "status": "success",
                "total": len(events),
                "events": events
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EventDetail(APIView):
    """Get, update, or delete specific event"""
    
    def get(self, request, event_id):
        """Get event details"""
        try:
            event = events_collection.find_one({"event_id": event_id, "deleted_yn": 0}, {"_id": 0})
            
            if not event:
                return JsonResponse({
                    "status": "error",
                    "message": "Event not found"
                }, status=404)
            
            # Convert datetime
            if event.get("created_date"):
                event["created_date"] = event["created_date"].isoformat()
            if event.get("modified_date"):
                event["modified_date"] = event["modified_date"].isoformat()
            
            return JsonResponse({
                "status": "success",
                "event": event
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def put(self, request, event_id):
        """Update event"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            event = events_collection.find_one({"event_id": event_id, "deleted_yn": 0})
            if not event:
                return JsonResponse({
                    "status": "error",
                    "message": "Event not found"
                }, status=404)
            
            update_fields = {}
            if "title" in data:
                update_fields["title"] = data["title"]
            if "description" in data:
                update_fields["description"] = data["description"]
            if "event_type" in data:
                update_fields["event_type"] = data["event_type"].upper()
            if "event_date" in data:
                update_fields["event_date"] = data["event_date"]
            if "start_time" in data:
                update_fields["start_time"] = data["start_time"]
            if "end_time" in data:
                update_fields["end_time"] = data["end_time"]
            if "location" in data:
                update_fields["location"] = data["location"]
            
            update_fields["modified_date"] = datetime.utcnow()
            
            events_collection.update_one(
                {"event_id": event_id},
                {"$set": update_fields}
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Event updated successfully"
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def delete(self, request, event_id):
        """Soft delete event"""
        try:
            event = events_collection.find_one({"event_id": event_id, "deleted_yn": 0})
            if not event:
                return JsonResponse({
                    "status": "error",
                    "message": "Event not found"
                }, status=404)
            
            events_collection.update_one(
                {"event_id": event_id},
                {"$set": {"deleted_yn": 1, "modified_date": datetime.utcnow()}}
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Event deleted successfully"
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class UpcomingEvents(APIView):
    """Get upcoming events in next 30 days"""
    
    def get(self, request):
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            
            events = list(events_collection.find({
                "deleted_yn": 0,
                "event_date": {"$gte": today, "$lte": future_date}
            }, {"_id": 0}).sort("event_date", 1))
            
            # Convert datetime
            for event in events:
                if event.get("created_date"):
                    event["created_date"] = event["created_date"].isoformat()
                if event.get("modified_date"):
                    event["modified_date"] = event["modified_date"].isoformat()
            
            return JsonResponse({
                "status": "success",
                "total": len(events),
                "events": events
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


# --------------------------
# KUDOS/RECOGNITION WALL APIs
# --------------------------
@method_decorator(csrf_exempt, name='dispatch')
class KudosWall(APIView):
    """Post and view kudos"""
    
    def post(self, request):
        """Post new kudos"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            from_emp_id = data.get("from_emp_id")
            to_emp_id = data.get("to_emp_id")
            message = data.get("message")
            
            if not all([from_emp_id, to_emp_id, message]):
                return JsonResponse({
                    "status": "error",
                    "message": "from_emp_id, to_emp_id, and message are required"
                }, status=400)
            
            # Verify both employees exist
            from_emp = employee_collection.find_one({"emp_id": from_emp_id, "deleted_yn": 0})
            to_emp = employee_collection.find_one({"emp_id": to_emp_id, "deleted_yn": 0})
            
            if not from_emp:
                return JsonResponse({
                    "status": "error",
                    "message": "Sender employee not found"
                }, status=404)
            
            if not to_emp:
                return JsonResponse({
                    "status": "error",
                    "message": "Recipient employee not found"
                }, status=404)
            
            kudos_id = generate_kudos_id()
            
            kudos_data = {
                "kudos_id": kudos_id,
                "from_emp_id": from_emp_id,
                "from_emp_name": from_emp.get("name"),
                "to_emp_id": to_emp_id,
                "to_emp_name": to_emp.get("name"),
                "message": message,
                "likes": [],
                "comments": [],
                "created_date": datetime.utcnow(),
                "deleted_yn": 0
            }
            
            kudos_collection.insert_one(kudos_data)
            
            return JsonResponse({
                "status": "success",
                "message": "Kudos posted successfully",
                "kudos_id": kudos_id
            }, status=201)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def get(self, request):
        """Get all kudos (wall view)"""
        try:
            kudos_list = list(kudos_collection.find({"deleted_yn": 0}, {"_id": 0}).sort("created_date", -1))
            
            # Convert datetime and add counts
            for kudos in kudos_list:
                if kudos.get("created_date"):
                    kudos["created_date"] = kudos["created_date"].isoformat()
                
                # Convert comment dates
                for comment in kudos.get("comments", []):
                    if comment.get("created_date"):
                        comment["created_date"] = comment["created_date"].isoformat()
                
                kudos["likes_count"] = len(kudos.get("likes", []))
                kudos["comments_count"] = len(kudos.get("comments", []))
            
            return JsonResponse({
                "status": "success",
                "total": len(kudos_list),
                "kudos": kudos_list
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class KudosDetail(APIView):
    """Get kudos details or kudos by employee"""
    
    def get(self, request, kudos_id=None, emp_id=None):
        """Get specific kudos or kudos received/given by employee"""
        try:
            if kudos_id:
                # Get specific kudos
                kudos = kudos_collection.find_one({"kudos_id": kudos_id, "deleted_yn": 0}, {"_id": 0})
                
                if not kudos:
                    return JsonResponse({
                        "status": "error",
                        "message": "Kudos not found"
                    }, status=404)
                
                # Convert datetime
                if kudos.get("created_date"):
                    kudos["created_date"] = kudos["created_date"].isoformat()
                
                for comment in kudos.get("comments", []):
                    if comment.get("created_date"):
                        comment["created_date"] = comment["created_date"].isoformat()
                
                kudos["likes_count"] = len(kudos.get("likes", []))
                kudos["comments_count"] = len(kudos.get("comments", []))
                
                return JsonResponse({
                    "status": "success",
                    "kudos": kudos
                }, status=200)
            
            elif emp_id:
                # Get kudos for specific employee (received or given)
                filter_type = request.GET.get("type", "received")  # received or given
                
                if filter_type == "received":
                    query = {"to_emp_id": emp_id, "deleted_yn": 0}
                else:
                    query = {"from_emp_id": emp_id, "deleted_yn": 0}
                
                kudos_list = list(kudos_collection.find(query, {"_id": 0}).sort("created_date", -1))
                
                # Convert datetime
                for kudos in kudos_list:
                    if kudos.get("created_date"):
                        kudos["created_date"] = kudos["created_date"].isoformat()
                    kudos["likes_count"] = len(kudos.get("likes", []))
                    kudos["comments_count"] = len(kudos.get("comments", []))
                
                return JsonResponse({
                    "status": "success",
                    "type": filter_type,
                    "total": len(kudos_list),
                    "kudos": kudos_list
                }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class KudosLike(APIView):
    """Like/unlike kudos"""
    
    def post(self, request, kudos_id):
        """Toggle like on kudos"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            emp_id = data.get("emp_id")
            
            if not emp_id:
                return JsonResponse({
                    "status": "error",
                    "message": "emp_id is required"
                }, status=400)
            
            # Verify employee exists
            emp = employee_collection.find_one({"emp_id": emp_id, "deleted_yn": 0})
            if not emp:
                return JsonResponse({
                    "status": "error",
                    "message": "Employee not found"
                }, status=404)
            
            # Find kudos
            kudos = kudos_collection.find_one({"kudos_id": kudos_id, "deleted_yn": 0})
            if not kudos:
                return JsonResponse({
                    "status": "error",
                    "message": "Kudos not found"
                }, status=404)
            
            likes = kudos.get("likes", [])
            
            if emp_id in likes:
                # Unlike
                kudos_collection.update_one(
                    {"kudos_id": kudos_id},
                    {"$pull": {"likes": emp_id}}
                )
                action = "unliked"
            else:
                # Like
                kudos_collection.update_one(
                    {"kudos_id": kudos_id},
                    {"$push": {"likes": emp_id}}
                )
                action = "liked"
            
            # Get updated count
            updated_kudos = kudos_collection.find_one({"kudos_id": kudos_id})
            likes_count = len(updated_kudos.get("likes", []))
            
            return JsonResponse({
                "status": "success",
                "message": f"Kudos {action}",
                "action": action,
                "likes_count": likes_count
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class KudosComment(APIView):
    """Add comment to kudos"""
    
    def post(self, request, kudos_id):
        """Add comment"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            emp_id = data.get("emp_id")
            comment_text = data.get("comment")
            
            if not all([emp_id, comment_text]):
                return JsonResponse({
                    "status": "error",
                    "message": "emp_id and comment are required"
                }, status=400)
            
            # Verify employee exists
            emp = employee_collection.find_one({"emp_id": emp_id, "deleted_yn": 0})
            if not emp:
                return JsonResponse({
                    "status": "error",
                    "message": "Employee not found"
                }, status=404)
            
            # Find kudos
            kudos = kudos_collection.find_one({"kudos_id": kudos_id, "deleted_yn": 0})
            if not kudos:
                return JsonResponse({
                    "status": "error",
                    "message": "Kudos not found"
                }, status=404)
            
            comment_id = generate_comment_id()
            
            comment_data = {
                "comment_id": comment_id,
                "emp_id": emp_id,
                "emp_name": emp.get("name"),
                "comment": comment_text,
                "created_date": datetime.utcnow()
            }
            
            kudos_collection.update_one(
                {"kudos_id": kudos_id},
                {"$push": {"comments": comment_data}}
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Comment added successfully",
                "comment_id": comment_id
            }, status=201)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


# --------------------------
# ANNOUNCEMENTS BOARD APIs
# --------------------------
@method_decorator(csrf_exempt, name='dispatch')
class AnnouncementsBoard(APIView):
    """Create and view announcements"""
    
    def post(self, request):
        """Create announcement (HR/Manager only)"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            title = data.get("title")
            content = data.get("content")
            priority = data.get("priority", "MEDIUM")  # LOW, MEDIUM, HIGH
            posted_by = data.get("posted_by")
            target_audience = data.get("target_audience", "ALL")  # ALL, EMPLOYEE, HR, MANAGER
            
            if not all([title, content, posted_by]):
                return JsonResponse({
                    "status": "error",
                    "message": "title, content, and posted_by are required"
                }, status=400)
            
            # Verify poster exists and has permission
            poster = employee_collection.find_one({"emp_id": posted_by, "deleted_yn": 0})
            if not poster:
                return JsonResponse({
                    "status": "error",
                    "message": "Poster employee not found"
                }, status=404)
            
            poster_role = poster.get("role", "EMPLOYEE").upper()
            
            # Only HR and Manager can post announcements
            if poster_role not in ["HR", "MANAGER"]:
                return JsonResponse({
                    "status": "error",
                    "message": "Only HR and Manager can post announcements"
                }, status=403)
            
            # Validate priority
            valid_priorities = ["LOW", "MEDIUM", "HIGH"]
            if priority.upper() not in valid_priorities:
                return JsonResponse({
                    "status": "error",
                    "message": f"Invalid priority. Use: {', '.join(valid_priorities)}"
                }, status=400)
            
            announcement_id = generate_announcement_id()
            
            announcement_data = {
                "announcement_id": announcement_id,
                "title": title,
                "content": content,
                "priority": priority.upper(),
                "posted_by": posted_by,
                "posted_by_name": poster.get("name"),
                "posted_by_role": poster_role,
                "target_audience": target_audience.upper(),
                "is_pinned": False,
                "created_date": datetime.utcnow(),
                "modified_date": datetime.utcnow(),
                "deleted_yn": 0
            }
            
            announcements_collection.insert_one(announcement_data)
            
            return JsonResponse({
                "status": "success",
                "message": "Announcement posted successfully",
                "announcement_id": announcement_id
            }, status=201)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def get(self, request):
        """Get all announcements"""
        try:
            # Get query parameters
            priority = request.GET.get("priority")
            target = request.GET.get("target")
            
            query = {"deleted_yn": 0}
            
            if priority:
                query["priority"] = priority.upper()
            
            if target:
                query["target_audience"] = target.upper()
            
            # Get pinned first, then others by date
            pinned = list(announcements_collection.find({**query, "is_pinned": True}, {"_id": 0}).sort("created_date", -1))
            regular = list(announcements_collection.find({**query, "is_pinned": False}, {"_id": 0}).sort("created_date", -1))
            
            announcements = pinned + regular
            
            # Convert datetime
            for ann in announcements:
                if ann.get("created_date"):
                    ann["created_date"] = ann["created_date"].isoformat()
                if ann.get("modified_date"):
                    ann["modified_date"] = ann["modified_date"].isoformat()
            
            return JsonResponse({
                "status": "success",
                "total": len(announcements),
                "pinned_count": len(pinned),
                "announcements": announcements
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AnnouncementDetail(APIView):
    """Get, update, or delete announcement"""
    
    def get(self, request, announcement_id):
        """Get announcement details"""
        try:
            announcement = announcements_collection.find_one(
                {"announcement_id": announcement_id, "deleted_yn": 0},
                {"_id": 0}
            )
            
            if not announcement:
                return JsonResponse({
                    "status": "error",
                    "message": "Announcement not found"
                }, status=404)
            
            # Convert datetime
            if announcement.get("created_date"):
                announcement["created_date"] = announcement["created_date"].isoformat()
            if announcement.get("modified_date"):
                announcement["modified_date"] = announcement["modified_date"].isoformat()
            
            return JsonResponse({
                "status": "success",
                "announcement": announcement
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def put(self, request, announcement_id):
        """Update announcement"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            announcement = announcements_collection.find_one(
                {"announcement_id": announcement_id, "deleted_yn": 0}
            )
            if not announcement:
                return JsonResponse({
                    "status": "error",
                    "message": "Announcement not found"
                }, status=404)
            
            update_fields = {}
            if "title" in data:
                update_fields["title"] = data["title"]
            if "content" in data:
                update_fields["content"] = data["content"]
            if "priority" in data:
                update_fields["priority"] = data["priority"].upper()
            if "target_audience" in data:
                update_fields["target_audience"] = data["target_audience"].upper()
            
            update_fields["modified_date"] = datetime.utcnow()
            
            announcements_collection.update_one(
                {"announcement_id": announcement_id},
                {"$set": update_fields}
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Announcement updated successfully"
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def delete(self, request, announcement_id):
        """Soft delete announcement"""
        try:
            announcement = announcements_collection.find_one(
                {"announcement_id": announcement_id, "deleted_yn": 0}
            )
            if not announcement:
                return JsonResponse({
                    "status": "error",
                    "message": "Announcement not found"
                }, status=404)
            
            announcements_collection.update_one(
                {"announcement_id": announcement_id},
                {"$set": {"deleted_yn": 1, "modified_date": datetime.utcnow()}}
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Announcement deleted successfully"
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class PinAnnouncement(APIView):
    """Pin/unpin announcement"""
    
    def post(self, request, announcement_id):
        """Toggle pin status"""
        try:
            data = json.loads(request.body.decode('utf-8'))
            pin_status = data.get("pin", True)  # True to pin, False to unpin
            
            announcement = announcements_collection.find_one(
                {"announcement_id": announcement_id, "deleted_yn": 0}
            )
            if not announcement:
                return JsonResponse({
                    "status": "error",
                    "message": "Announcement not found"
                }, status=404)
            
            announcements_collection.update_one(
                {"announcement_id": announcement_id},
                {"$set": {"is_pinned": pin_status, "modified_date": datetime.utcnow()}}
            )
            
            action = "pinned" if pin_status else "unpinned"
            
            return JsonResponse({
                "status": "success",
                "message": f"Announcement {action} successfully",
                "is_pinned": pin_status
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class PinnedAnnouncements(APIView):
    """Get only pinned announcements"""
    
    def get(self, request):
        try:
            announcements = list(announcements_collection.find(
                {"deleted_yn": 0, "is_pinned": True},
                {"_id": 0}
            ).sort("created_date", -1))
            
            # Convert datetime
            for ann in announcements:
                if ann.get("created_date"):
                    ann["created_date"] = ann["created_date"].isoformat()
                if ann.get("modified_date"):
                    ann["modified_date"] = ann["modified_date"].isoformat()
            
            return JsonResponse({
                "status": "success",
                "total": len(announcements),
                "announcements": announcements
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
