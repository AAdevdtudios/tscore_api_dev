from django.db import models
from django.conf import settings
from ckeditor.fields import RichTextField

# from tinymce import HTMLField


# Create your models here.
class Notifications(models.Model):
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=256)
    content = RichTextField(blank=True, null=True)

    def __str__(self):
        return self.title
