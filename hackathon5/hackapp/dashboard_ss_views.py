from rest_framework.views import APIView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from pymongo import MongoClient
from datetime import datetime, timedelta
import json

# MongoDB Connection
client = MongoClient("mongodb+srv://akalyabharath20_db_user:LVyhweJauTGaO0pp@cluster0.2ss7wcx.mongodb.net/")
db = client["test"]
employee_collection = db["employees"]
events_collection = db["events"]
kudos_collection = db["kudos"]


@method_decorator(csrf_exempt, name='dispatch')
class DashboardSSAPI(APIView):
    """Combined dashboard API - Returns upcoming events, recent kudos, and birthdays in one call"""
    
    def get(self, request):
        try:
            today = datetime.now()
            
            # --------------------------
            # 1. UPCOMING EVENTS (Next 30 days)
            # --------------------------
            future_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
            today_str = today.strftime("%Y-%m-%d")
            
            upcoming_events = list(events_collection.find({
                "deleted_yn": 0,
                "event_date": {"$gte": today_str, "$lte": future_date}
            }, {
                "_id": 0,
                "event_id": 1,
                "title": 1,
                "event_type": 1,
                "event_date": 1,
                "location": 1
            }).sort("event_date", 1).limit(5))
            
            # Calculate days until each event
            for event in upcoming_events:
                event_date = datetime.strptime(event["event_date"], "%Y-%m-%d")
                days_until = (event_date - today).days
                event["days_until"] = days_until
            
            # --------------------------
            # 2. RECENT KUDOS (Last 5)
            # --------------------------
            recent_kudos = list(kudos_collection.find({
                "deleted_yn": 0
            }, {
                "_id": 0,
                "kudos_id": 1,
                "from_emp_name": 1,
                "to_emp_name": 1,
                "message": 1,
                "likes": 1,
                "comments": 1,
                "created_date": 1
            }).sort("created_date", -1).limit(5))
            
            # Add counts and convert datetime
            for kudos in recent_kudos:
                kudos["likes_count"] = len(kudos.get("likes", []))
                kudos["comments_count"] = len(kudos.get("comments", []))
                if kudos.get("created_date"):
                    kudos["created_date"] = kudos["created_date"].isoformat()
                # Remove full arrays to reduce response size
                kudos.pop("likes", None)
                kudos.pop("comments", None)
            
            # --------------------------
            # 3. UPCOMING BIRTHDAYS (Next 7 days)
            # --------------------------
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
                    
                    # Check if birthday is within next 7 days
                    days_until = (this_year_birthday - today).days
                    
                    if 0 <= days_until <= 7:
                        upcoming_birthdays.append({
                            "emp_id": emp.get("emp_id"),
                            "name": emp.get("name"),
                            "birthday_date": this_year_birthday.strftime("%Y-%m-%d"),
                            "days_until": days_until
                        })
                except:
                    continue
            
            # Sort by days_until
            upcoming_birthdays.sort(key=lambda x: x["days_until"])
            
            # --------------------------
            # COMBINED RESPONSE
            # --------------------------
            return JsonResponse({
                "status": "success",
                "dashboard": {
                    "upcoming_events": {
                        "total": len(upcoming_events),
                        "events": upcoming_events
                    },
                    "recent_kudos": {
                        "total": len(recent_kudos),
                        "kudos": recent_kudos
                    },
                    "birthdays": {
                        "total": len(upcoming_birthdays),
                        "birthdays": upcoming_birthdays
                    }
                }
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
