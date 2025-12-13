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
from hackapp.views import (welcome,EmployeeAPI, EmployeeUpdateView, EmployeeDeleteView,SignIn,SignOut,GrievanceAPI, GetGrievanceView,
                           HRReplyGrievanceView,TaskCreateAssignAPI,UpdateTaskView,TaskListByEmployeeAPI,TaskDeleteAPI,empoyeedropdown,
                           DashboardAPI)
from hackapp.attendance_leave_views import (
    AttendanceCheckInOut, AttendanceHistory, MonthlyAttendanceReport,
    LeaveBalance, LeaveApplication, LeaveApproval, ManagerLeaveRequests,
    ManagerAttendanceDashboard
)
from hackapp.events_engagement_views import (
    UpcomingBirthdays, TodayBirthdays,
    EventCalendar, EventDetail, UpcomingEvents,
    KudosWall, KudosDetail, KudosLike, KudosComment,
    AnnouncementsBoard, AnnouncementDetail, PinAnnouncement, PinnedAnnouncements
)
from hackapp.travel_expense_views import (
    TravelRequest, TravelRequestDetail, TravelApproval,
    ExpenseSubmission, ExpenseDetail, ExpenseReceipt,
    ExpenseApproval, ExpenseReimbursement, ReimbursementSummary
)
from hackapp.dashboard_ss_views import DashboardSSAPI
from hackapp.asset_management_views import (
    AssetManagementAPI, AssetAssignmentAPI, AssetDashboardAPI
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
    path("api/grievance/", GrievanceAPI.as_view(), name="grievance-api"),
    path("api/grievance/get/<str:user_id>/", GetGrievanceView.as_view(), name="get-grievances"),
    path("grievance/reply/<str:grievance_id>/<str:hr_id>/", HRReplyGrievanceView.as_view()),
    path("api/task_creation/", TaskCreateAssignAPI.as_view(), name="tasks-api"),    
    path("api/task_update/<str:task_id>/", UpdateTaskView.as_view(), name="task-update-api"),
    path("api/task/<str:emp_id>/", TaskListByEmployeeAPI.as_view(), name="get-tasks-api"),
    path("api/delete_task/<task_id>/", TaskDeleteAPI.as_view(), name="get-all-tasks-api"),
    path("api/emp_dropdown/", empoyeedropdown.as_view(), name="employee-dropdown"),
    path("api/dashboard/<str:user_id>/", DashboardAPI.as_view(), name="dashboard-api"),
    
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
    
    # Manager Attendance Dashboard
    path("api/attendance/manager/dashboard/", ManagerAttendanceDashboard.as_view()),
    
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
    
    # Travel Request APIs
    path("api/travel/request/", TravelRequest.as_view()),
    path("api/travel/request/<str:travel_id>", TravelRequestDetail.as_view()),
    path("api/travel/request/<str:travel_id>/approve/", TravelApproval.as_view()),
    
    # Expense Management APIs
    path("api/expense/submit/", ExpenseSubmission.as_view()),
    path("api/expense/", ExpenseSubmission.as_view()),
    path("api/expense/<str:expense_id>", ExpenseDetail.as_view()),
    path("api/expense/<str:expense_id>/receipt/", ExpenseReceipt.as_view()),
    path("api/expense/<str:expense_id>/approve/", ExpenseApproval.as_view()),
    path("api/expense/<str:expense_id>/reimburse/", ExpenseReimbursement.as_view()),
    path("api/expense/reimbursement/summary/<str:emp_id>", ReimbursementSummary.as_view()),
    
    # Dashboard SS API (Combined)
    path("api/dashboard_ss/", DashboardSSAPI.as_view()),
    
    # Asset Management APIs (Task 8)
    path("api/assets/", AssetManagementAPI.as_view()),
    path("api/assets/assign/", AssetAssignmentAPI.as_view()),
    path("api/assets/dashboard/", AssetDashboardAPI.as_view()),
]
