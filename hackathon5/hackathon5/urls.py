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
                           HRReplyGrievanceView,TaskCreateAssignAPI,TaskUpdateAPI,TaskListByEmployeeAPI,TaskDeleteAPI)
from hackapp.attendance_leave_views import (
    AttendanceCheckInOut, AttendanceHistory, MonthlyAttendanceReport,
    LeaveBalance, LeaveApplication, LeaveApproval, ManagerLeaveRequests
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
    path("api/task_update/<str:task_id>/", TaskUpdateAPI.as_view(), name="task-update-api"),
    path("api/task/<str:emp_id>/", TaskListByEmployeeAPI.as_view(), name="get-tasks-api"),
    path("api/delete_task/<task_id>/", TaskDeleteAPI.as_view(), name="get-all-tasks-api"),
    
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
]
