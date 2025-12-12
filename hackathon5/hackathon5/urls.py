"""
URL configuration for hackathon5 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from hackapp.views import welcome,EmployeeAPI, EmployeeUpdateView, EmployeeDeleteView,SignIn,SignOut,GrievanceAPI
from hackapp.attendance_leave_views import (
    AttendanceCheckInOut, AttendanceHistory, MonthlyAttendanceReport,
    LeaveBalance, LeaveApplication, LeaveApproval, ManagerLeaveRequests
)
from hackapp.events_engagement_views import (
    UpcomingBirthdays, TodayBirthdays,
    EventCalendar, EventDetail, UpcomingEvents,
    KudosWall, KudosDetail, KudosLike, KudosComment,
    AnnouncementsBoard, AnnouncementDetail, PinAnnouncement, PinnedAnnouncements
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', welcome, name='welcome'),
    path('api/employee/', EmployeeAPI.as_view(), name='employee_api'),  
    path("api/employee/<str:emp_oid>", EmployeeAPI.as_view()),
    path("api/employee/update/<str:emp_oid>", EmployeeUpdateView.as_view()),  # UPDATE
    path("api/employee/delete/<str:emp_oid>", EmployeeDeleteView.as_view()),
    path("api/signin/", SignIn.as_view()),
    path("api/signout/", SignOut.as_view()),
    
    # Attendance APIs
    path("api/attendance/checkinout/", AttendanceCheckInOut.as_view()),
    path("api/attendance/history/<str:emp_id>", AttendanceHistory.as_view()),
    path("api/attendance/report/<str:emp_id>", MonthlyAttendanceReport.as_view()),
    
    # Leave Management APIs
    path("api/leave/balance/<str:emp_id>", LeaveBalance.as_view()),
    path("api/leave/apply/", LeaveApplication.as_view()),
    path("api/leave/applications/<str:emp_id>", LeaveApplication.as_view()),
    path("api/leave/approve/<str:leave_id>", LeaveApproval.as_view()),
    path("api/leave/manager/requests/", ManagerLeaveRequests.as_view()),
    
    # Birthdays APIs
    path("api/events/birthdays/upcoming/", UpcomingBirthdays.as_view()),
    path("api/events/birthdays/today/", TodayBirthdays.as_view()),
    
    # Event Calendar APIs
    path("api/events/calendar/", EventCalendar.as_view()),
    path("api/events/calendar/<str:event_id>", EventDetail.as_view()),
    path("api/events/calendar/upcoming/", UpcomingEvents.as_view()),
    
    # Kudos/Recognition Wall APIs
    path("api/events/kudos/", KudosWall.as_view()),
    path("api/events/kudos/<str:kudos_id>", KudosDetail.as_view()),
    path("api/events/kudos/<str:kudos_id>/like/", KudosLike.as_view()),
    path("api/events/kudos/<str:kudos_id>/comment/", KudosComment.as_view()),
    path("api/events/kudos/received/<str:emp_id>", KudosDetail.as_view()),
    path("api/events/kudos/given/<str:emp_id>", KudosDetail.as_view()),
    
    # Announcements Board APIs
    path("api/events/announcements/", AnnouncementsBoard.as_view()),
    path("api/events/announcements/<str:announcement_id>", AnnouncementDetail.as_view()),
    path("api/events/announcements/<str:announcement_id>/pin/", PinAnnouncement.as_view()),
    path("api/events/announcements/pinned/", PinnedAnnouncements.as_view()),
]
