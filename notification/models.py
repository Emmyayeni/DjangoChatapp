from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# Create your models here.

class Notification(models.Model):
    # who the notification is sent to
    target = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    # the user that the creation of the notification was triggered by
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,null=True,blank=True,related_name="from_user")
    # the redirect url the url that the notification when clicked will redirect to
    redirect_url = models.URLField(max_length=500,null=True,unique=False,blank=True,help_text="The URL to redirect to when clicked")
    # statement describing the notification (ex: Mitch sent you a friend request)
    verb = models.CharField(max_length=500,unique=False,blank=True,null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    
    content_type = models.ForeignKey(ContentType,on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    def __str__(self):
        return self.verb

    def get_content_object_type(self):
        return str(self.get_content_object_type.get_cname)
