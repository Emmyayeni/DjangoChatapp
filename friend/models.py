from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from chat.utils import find_or_create_private_chat
from notification.models import Notification

class FriendList(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE, related_name="user")
    friends = models.ManyToManyField(settings.AUTH_USER_MODEL,blank=True,related_name="friends")
    
    # for reverse lookups
    notifications = GenericRelation(Notification)

    def __str__(self):
        return self.user.username

    def add_friend(self,account):
        """
            ADD A NEW FRIEND 
        """
        if not account in self.friends.all():
            self.friends.add(account)
            self.save()
            chat = find_or_create_private_chat(self.user,account)
            if not chat.is_active:
                chat.is_active = True
                chat.save()

    def remove_friend(self,account):
        """
            Remove a friend 
        """
        if account in self.friends.all():
            self.friends.remove(account)
            chat = find_or_create_private_chat(self.user,account)
            if not chat.is_active:
                chat.is_active = False
                chat.save()
                
    def unfriend(self,removee):
        """
         Initiate the action of unfriending someone
        """
          # person terminating the freindship
        remover_friends_list = self   
      
        
        # Remove friend from removee friend list
        remover_friends_list.remove_friend(removee)

        # remove friend from removee friend list
        friend_list = FriendList.objects.get(user=removee)
        friend_list.remove_friend(self.user)

    def is_mutual_friend(self,friend):
        """
            is this a friend
        
        """
        if friend in self.friends.all():
            return True
        return False
    
    @property
    def get_cname(self):
        """
        For determining what kind of object is associated with a Notification
        """
        return "FriendList"

class FriendRequest(models.Model):
    """
        A friend request consists of two main part 
        1.SENDER:
            - Person sending/initaiating the friend request
        2.SENDER:
          - Person recieving the friend request
    """
    sender = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE, related_name="receiver")
    is_active = models.BooleanField(blank=True,null=False,default=True)

    timestamp = models.DateTimeField(auto_now_add=True)
    notifications = GenericRelation(Notification)

    def __str__(self):
        return self.sender.username

    def accept(self):
        """
           Accept a freind request
           Update both SENDER and RECEIVER friend lists 
        """
        receiver_friend_list = FriendList.objects.get(user=self.receiver)
        if receiver_friend_list:
            receiver_friend_list.add_friend(self.sender)
            sender_friend_list = FriendList.objects.get(user=self.sender)
            if sender_friend_list:
                sender_friend_list.add_friend(self.receiver)
                self.is_active = False
                self.save()
    def decline(self):
        """
            Decline a friend request
            it is  'declined" by setting the 'active' field to false 
        """
        self.is_active = False
        self.save()

    def cancel(self):

        """
            Cancel a friend request
            It is 'cancelled' by setting the 'is_active' to False.
            This is only different with respect to 'declining' through the notification that 
            is generated
        """  

        self.is_active = False
        self.save()

        
    @property
    def get_cname(self):
        """
        For determining what kind of object is associated with a Notification
        """
        return "FriendRequest"
