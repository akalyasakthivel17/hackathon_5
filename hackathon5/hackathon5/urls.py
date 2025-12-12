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
from hackapp.views import welcome,EmployeeAPI, EmployeeUpdateView, EmployeeDeleteView,SignIn,SignOut

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', welcome, name='welcome'),
    path('api/employee/', EmployeeAPI.as_view(), name='employee_api'),  
    path("api/employee/<str:emp_oid>", EmployeeAPI.as_view()),
    path("api/employee/update/<str:emp_oid>", EmployeeUpdateView.as_view()),  # UPDATE
    path("api/employee/delete/<str:emp_oid>", EmployeeDeleteView.as_view()),
    path("api/signin/", SignIn.as_view()),
    path("api/signout/", SignOut.as_view()),
]
