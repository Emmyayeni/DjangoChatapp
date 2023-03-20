from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from chat.utils import find_or_create_private_chat
from notification.models import Notification
from django.db.models.signals import post_save
from django.dispatch import receiver

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
            # the content_type 
            content_type    =ContentType.objects.get_for_model(self)
            # creating the notification 
            # Notification(
            #     target = self.user,
            #     from_user = account,
            #     redirect_url = f"{settings.BASE_URL}/account/{account.pk}",
            #     verb = f"You are now friends with {account.username}.",
            #     content_type = content_type,
            #     object_id=self.id
            # ).save()
            self.notifications.create(
                target = self.user,
                from_user = account,
                redirect_url = f"{settings.BASE_URL}/account/{account.pk}",
                verb = f"You are now friends with {account.username}.",
                content_type = content_type,
            )
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

        content_type = ContentType.objects.get_for_model(self)

        self.notifications.create(
                target = removee,
                from_user = self.user,
                redirect_url = f"{settings.BASE_URL}/account/{self.user.pk}",
                verb = f"You are no longer friends with {self.user.username}.",
                content_type = content_type,
        )
        self.save()
    
    
    @property
    def get_cname(self):
        """
        For determining what kind of object is associated with a Notification
        """
        return "FriendList"
        
    def is_mutual_friend(self,friend):
        """
            is this a friend
        
        """
        if friend in self.friends.all():
            return True
        return False
   

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
            content_type = ContentType.objects.get_for_model(self)
            #Update notification for receiver 
            receiver_notification = Notification.objects.get(target=self.receiver,content_type=content_type,object_id=self.id)
            receiver_notification.is_active = False
            receiver_notification.redirect_url = f"{settings.BASE_URL}/account/{self.sender.pk}"
            receiver_notification.verb = f"You accepted {self.sender.username}'s friend request"
            receiver_notification.timestamp = timezone.now()
            receiver_notification.save()
            receiver_friend_list.add_friend(self.sender)
            sender_friend_list = FriendList.objects.get(user=self.sender)
            if sender_friend_list:
                #create notification for sender 
                        
                self.notifications.create(
                    target = self.sender,
                    from_user = self.receiver,
                    redirect_url = f"{settings.BASE_URL}/account/{self.receiver.pk}",
                    verb = f"{self.receiver.username} accepted your friend request.",
                    content_type = content_type,
                )
                sender_friend_list.add_friend(self.receiver)
                self.is_active = False
                self.save()
        return receiver_notification
                     
    def decline(self):
        """
            Decline a friend request
            it is  'declined" by setting the 'active' field to false 
        """
        content_type = ContentType.objects.get_for_model(self)
            #Update notification for receiver 
        notification = Notification.objects.get(target=self.receiver,content_type=content_type,object_id=self.id)
        notification.is_active = False
        notification.redirect_url = f"{settings.BASE_URL}/account/{self.sender.pk}"
        notification.verb = f"You declined {self.sender.username}'s friend request"
        notification.timestamp = timezone.now()
        notification.save()

        self.notifications.create(
            target = self.sender,
            from_user = self.receiver,
            redirect_url = f"{settings.BASE_URL}/account/{self.receiver.pk}",
            verb = f"{self.receiver.username} declined your friend request.",
            content_type = content_type,
        )
        return notification

    def cancel(self):
        self.is_active = False
        self.save()
        content_type = ContentType.objects.get_for_model(self)
        #Update notification for receiver 
        receiver_notification = Notification.objects.get(target=self.receiver,content_type=content_type,object_id=self.id)
        receiver_notification.is_active = False
        receiver_notification.redirect_url = f"{settings.BASE_URL}/account/{self.sender.pk}"
        receiver_notification.verb = f"{self.sender.username}'s cancelled the friend request sent to you"
         
        receiver_notification.save()

        self.notifications.create(
            target = self.sender,
            from_user = self.receiver,
            redirect_url = f"{settings.BASE_URL}/account/{self.receiver.pk}",
            verb = f"You cancelled the friend request you sent  {self.receiver.username}.",
            content_type = content_type,
        )
        return receiver_notification

        """
            Cancel a friend request
            It is 'cancelled' by setting the 'is_active' to False.
            This is only different with respect to 'declining' through the notification that 
            is generated
        """  
    @property
    def get_cname(self):
        """
        For determining what kind of object is associated with a Notification
        """
        return "FriendRequest"


@receiver(post_save,sender=FriendRequest)
def create_notification(sender,instance,created,**kwargs):
    if created:
        instance.notifications.create(
            target = instance.receiver,
            from_user = instance.sender,
            redirect_url =f"{settings.BASE_URL}/account/{instance.sender.pk}",
            verb =f"{instance.sender.username} sent you a friend request.",
            content_type=instance,
        )

