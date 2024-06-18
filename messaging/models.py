from django.db import models
from django.contrib.auth import get_user_model
from utils.tools import BaseModel, generate_reference_id
from .utils import message_pictures_path

# Create your models here.
User = get_user_model()

class CustomerMessage(BaseModel):
    reference_id = models.CharField(
        unique=True, editable=False, default=generate_reference_id
    )
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    message = models.TextField(null=False)
    pictures = models.ManyToManyField("Picture", related_name="message_pictures")
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Customers' Messages"
        verbose_name_plural = "Customers' Messages"
        abstract = False
        ordering = ["-date_created"]

    def assign_message_reference(self, *args, **kwargs):
        if self.message and not self.reference_id:
            self.reference_id = generate_reference_id()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.message[:25]} - {self.reference_id}"

class Picture(BaseModel):
    image = models.ImageField(null=True, upload_to=message_pictures_path)
    caption = models.CharField(max_length=200, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Messages' Pictures"
        verbose_name_plural = "Messages' Pictures"
        abstract = False
        ordering = ["-date_created"]
