
# Create your models here.
from django.db import models
from django.utils import timezone
import json


class Employee(models.Model):
    emp_id = models.CharField(max_length=20, unique=True)  # EMP001
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # hashed password
    role = models.CharField(max_length=50, default="EMPLOYEE")  # ADMIN / EMPLOYEE / MANAGER etc.

    # Storing base64 files in JSON format: [{"file_name": "...", "file_data": "..."}]
    documents = models.TextField(default="[]")

    deleted_yn = models.IntegerField(default=0)  # 0 = active, 1 = deleted

    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)

    def set_documents(self, docs_list):
        """Convert Python list to JSON string before saving"""
        self.documents = json.dumps(docs_list)

    def get_documents(self):
        """Return JSON string as Python list"""
        try:
            return json.loads(self.documents)
        except:
            return []

    def __str__(self):
        return f"{self.emp_id} - {self.name}"
