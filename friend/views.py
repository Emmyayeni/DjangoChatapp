from django.shortcuts import render,redirect
from django.http import HttpResponse
import json
# Create your views here.

from account.models import Account
from  friend.models import FriendRequest,FriendList

def friend_requests(request,*args,**kwargs):
    context = {}
    user = request.user
    if user.is_authenticated:
        user_id = kwargs.get("user_id")
        account = Account.objects.get(pk=user_id)
        if account == user:
            friend_requests = FriendRequest.objects.filter(receiver=account,is_active=True)
            accounts = Account.objects.all()
            friend = FriendList.objects.get(user=account)
            all_friend = friend.friends.all()
            other_users = []
            for user in accounts:
                if user not in all_friend and user!=account:
                    other_users.append(user)
            context['friend_requests'] = friend_requests
            context['other_users'] = other_users
        else:
            return HttpResponse("You can't view another user friend request")
    redirect("login")

    return render(request, "friend/friend_requests.html",context)

def send_friend_request(request,*args,**kwargs):
    user = request.user
    payload = {}
    if request.method == "POST" and user.is_authenticated:
        user_id = request.POST.get("receiver_user_id")
        if user_id:
            receiver = Account.objects.get(pk=user_id)
            try:
				# Get any friend requests (active and not-active)
                friend_requests = FriendRequest.objects.filter(sender=user, receiver=receiver)
				# find if any of them are active (pending)
                try:
                    for request in friend_requests:
                        if request.is_active:
                            raise Exception("You already sent them a friend request.")
                     # If none are active create a new friend request
                    friend_request = FriendRequest(sender=user, receiver=receiver)
                    friend_request.save()
                    payload['response'] = "Friend request sent."
                except Exception as e:
                    payload['response'] = str(e)
            except FriendRequest.DoesNotExist:
				# There are no friend requests so create one.
                friend_request = FriendRequest(sender=user, receiver=receiver)
                friend_request.save()
                payload['response'] = "Friend request sent."

                if payload['response'] == None:
                    payload['response'] = "Something went wrong."
                else:
                    payload['response'] = "Unable to sent a friend request."
        else:
            payload['response'] = "You must be authenticated to send a friend request."
    return HttpResponse(json.dumps(payload), content_type="application/json")

def accept_friend_request(request, *args, **kwargs):
    user = request.user
    payload = {}
    if request.method == "GET" and user.is_authenticated:
        friend_request_id = kwargs.get("friend_request_id")
        if friend_request_id:
            friend_request = FriendRequest.objects.get(pk=friend_request_id)
                # confirm that is the correct request
            if friend_request.receiver == user:
                if friend_request: 
                        # found the request. Now accept it
                    friend_request.accept()
                    payload['response'] = "Friend request accepted."
                else:
                    payload['response'] = "Something went wrong."
            else:
                payload['response'] = "That is not your request to accept."
        else:
            payload['response'] = "Unable to accept that friend request."
    else:
        # should never happen
        payload['response'] = "You must be authenticated to accept a friend request."
    return HttpResponse(json.dumps(payload), content_type="application/json")

def remove_friend(request,*args,**kwargs):
    user = request.user 
    payload = {}
    if request.method == "POST" and user.is_authenticated:
        user_id = request.POST.get('receiver_user_id')
        if user_id :
            try:
                removee = Account.objects.get(pk=user_id)
                friend_list = FriendList.objects.get(user=user)
                friend_list.unfriend(removee)
                payload['response'] = "Successfully removed that friend."
            except Exception as e:
                payload['response'] = f"Something went wrong:{e}"
        else:
            payload['response'] = "There was an error. Unable to remove that friend."
    else:
        payload["response"] = "You must be authenticated to remove a friend"
    return HttpResponse(json.dumps(payload),content_type="application/json")

def decline_friend_request(request,*args,**kwargs):
    user = request.user 
    payload = {}
    if request.method == "GET" and user.is_authenticated:
        friend_request_id = kwargs.get("friend_request_id")
        if friend_request_id:
            friend_request = FriendRequest.objects.get(pk=friend_request_id)
            
            if friend_request.receiver == user:
                if friend_request:
                    friend_request.decline()
                    payload['response'] = "Friend request decline."
                else:
                    payload["response"] = "Something went wrong."
            else:
                payload["response"] = "That is not your request to decline"
        else:
            payload["response"] = "Unable to decline that friend request."
    else:
        payload["response"] = "You must be authenticated to decline a friend request. "
    return HttpResponse(json.dumps(payload),content_type="application/json")

def cancel_friend_request(request,*args, **kwargs):
    user = request.user
    payload = {}
    if request.method == "POST" and user.is_authenticated:
        user_id = request.POST.get("receiver_user_id")
        if user_id:
            receiver = Account.objects.get(pk=user_id)
            try:
                friend_requests = FriendRequest.objects.filter(sender=user, receiver=receiver, is_active=True)
            except FriendRequest.DoesNotExist:
                payload['response'] = "Nothing to cancel. Friend request does not exist."

			# There should only ever be ONE active friend request at any given time. Cancel them all just in case.
            if len(friend_requests) > 1:
                for request in friend_requests:
                    request.cancel()
                    payload['response'] = "Friend request canceled."
            else:
				# found the request. Now cancel it
                friend_requests.first().cancel()
                payload['response'] = "Friend request canceled."
        else:
            payload['response'] = "Unable to cancel that friend request."
    else:
		# should never happen
        payload['response'] = "You must be authenticated to cancel a friend request."
    return HttpResponse(json.dumps(payload), content_type="application/json")
























