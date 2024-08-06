from django.db import models
from django.contrib.auth.models import User

class UploadedPDF(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pdf_file = models.FileField(upload_to='pdfs/')
    text = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    image_urls = models.JSONField() 

    def __str__(self):
        return f"{self.user.username}'s PDF - {self.pdf_file.name}"
