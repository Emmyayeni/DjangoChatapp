from django.db import models
from django.conf import settings
# Create your models here.


class Topic(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class PublicChatRoom(models.Model):
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255,unique=True,blank=False)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='participants',blank=True,help_text="users who has joined the chat room")
    description = models.TextField(blank=True,null=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    active_users = models.ManyToManyField(settings.AUTH_USER_MODEL,related_name='active_users',blank=True,help_text="users who are connected to the chat")
    def __str__(self):

        return self.name


    # def connect_user(self,user):

    #     """
    #     return true if  user is added to the users list
    #     """
    #     is_user_added = False
    #     if user in self.participants:
    #         if not user in self.active_users.all():
    #             self.users.add(user)
    #             self.save()
    #             is_user_added = True
    #         elif user in self.active_users.all():
    #             is_user_added = True
    #         return is_user_added
    #     else:
    #         raise "you must be a participant of the group for you to be active"
    #     return 
    
    # def disconnect_user(self,user):
    #     """
    #     return true if user is removed from the user list
    #     """

    #     is_user_removed  = False
    #     if user in self.active_users.all():
    #         self.users.remove(user)
    #         self.save()
    #         is_user_removed = True
    #     elif user in self.users.all():
    #         is_user_removed =True
    #     return is_user_removed

    def add_user(self,user):
        self.participants.add(user)

    @property
    def group_name(self):
        """
        Returns the channels group name that sockets should subscribe to and get sent sent messages as they are generated
        """
        return f"PublicChatRoom-{self.id}"
        
class PublicRoomMessageManager(models.Manager):
    def by_room(self,room):
        qs = PublicRoomChatMessage.objects.filter(room=room).order_by("-timestamp")
        return qs

class PublicRoomChatMessage(models.Model):
    """
    chat message created by a user inside a publicChatRoom(foreign key)
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    room = models.ForeignKey(PublicChatRoom,on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField(unique=False,blank=False)

    objects = PublicRoomMessageManager()

    def __str__(self):
        return self.content


 