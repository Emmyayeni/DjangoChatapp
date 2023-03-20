from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth import login, authenticate,logout
from account.forms import RegistrationForm,AccountAuthenticationForm,AccountUpdateForm
# Create your views here.
from django.contrib import messages
from friend.models import *
from django.conf import settings
from account.models import *
from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage
import os
import cv2
import json
import base64
from django.core import files
from friend.util import get_friend_request_or_false
from friend.friend_request_status import *
from Publicchat.models import PublicChatRoom
TEMP_PROFILE_IMAGE_NAME = "temp_profile_image.png"

def register_view(request):
    form = RegistrationForm()

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data.get('email').lower()
            raw_password = form.cleaned_data.get('password1')
            account = authenticate(email=email, password=raw_password)
            login(request, account)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registration')

    return render(request, 'account/login.html', {'form': form})


def Login(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = Account.objects.get(email=email)
        except:
            messages.error(request, 'User does not exist')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username OR password does not exit')
    return render(request, 'account/login.html')



def logout_view(request):
    logout(request)
    return redirect("login")


def account_view(request,*args,**kwargs):
    """
    - logic here is kind of tricky 
    is_self (boolean)
        is_friend(boolean)
        -1:NO_REQUEST_SENT
        0:THEM_SENT_TO_YOU
        1:YOU_SENT_TO_THEM

    """
    context = {}
    user_id = kwargs.get("user_id")
    try:
        account = Account.objects.get(pk=user_id)
    except Account.DoesNotExist:
        return HttpResponse("that user doesn't exist.")
    if account:
        context['id'] = account.id
        context['username'] = account.username
        context['email'] = account.email
        context['profile_image'] = account.profile_image.url
        context['hide_email'] = account.hide_email
        room_host_by_user = PublicChatRoom.objects.filter(host=account)
        context['rooms'] = room_host_by_user
        try:
            friend_list = FriendList.objects.get(user=account)
        except FriendList.DoesNotExist:
            friend_list = FriendList(user=account)
            friend_list.save() 
        friends = friend_list.friends.all()
        context['friends'] = friends
        context['bio']=account.bio
        # define stae variables
        is_self = True
        request_sent = FriendRequestStatus.NO_REQUEST_SENT.value # range: ENUM -> friend/friend_request_status.FriendRequestStatus
        is_friend = False
        friend_requests = None
        user = request.user
        request_user_id = user.id
        if user.is_authenticated and user != account:
            is_self = False
            if friends.filter(pk=user.id):
                is_friend = True
            else:
                is_friend = False
                # CASE1: request has 
                if get_friend_request_or_false(sender=account, receiver=user) != False:
                    request_sent = FriendRequestStatus.THEM_SENT_TO_YOU.value
                    context['pending_friend_request_id'] = get_friend_request_or_false(sender=account, receiver=user).id
                # CASE 2: request has been sent from you to them 
                elif get_friend_request_or_false(sender=user, receiver=account) !=False:
                    request_sent = FriendRequestStatus.YOU_SENT_TO_THEM.value 
                else:   
                    request_sent = FriendRequestStatus.NO_REQUEST_SENT.value 
        elif not user.is_authenticated:
            is_self = False
        else:
            try: 
                friend_requests = FriendRequest.objects.filter(receiver=user,is_active=True)            
            except:
                pass
        context['is_self'] = is_self
        context['is_friend'] = is_friend
        context['BASE_URL'] = settings.BASE_URL
        context['request_sent'] = request_sent
        context['friend_requests'] = friend_requests
        context['request_user_id'] = request_user_id
        return render(request,'account/account.html',context)


def account_search_results(request,*args,**kwargs):
    context = {}
    if request.method == "GET":
        search_query = request.GET.get("q")
        if len(search_query) > 0:
            search_results = Account.objects.filter(email__icontains=search_query).filter(username__icontains=search_query).distinct()
            user = request.user
            accounts = [] # [(account1, True), (account2, False), ...]
            if user.is_authenticated:
    			# get the authenticated users friend list
                auth_user_friend_list = FriendList.objects.get(user=user)
                for account in search_results:
                    accounts.append((account, auth_user_friend_list.is_mutual_friend(account)))
                context['accounts'] = accounts
            else:
                for account in search_results:
                    accounts.append((account, False))
                context['accounts'] = accounts
    
    return render(request,'account/search_results.html',context)

    user = request.user
def edit_account(request,*args,**kwargs):
    if not request.user.is_authenticated:
       return redirect("login")
    user_id = kwargs.get("user_id") 
    try:
        account = Account.objects.get(pk=user_id)
    except Account.DoesNotExist:
        raise HttpResponse("something went wrong.")
    if account.pk !=request.user.pk:
        return HttpResponse("You cannot edit someone elses profile.")
    context = {}
    if request.POST:
        form = AccountUpdateForm(request.POST,request.FILES,instance=request.user)
        if form.is_valid():

            form.save()
            return redirect("account:view", user_id=account.pk)
            
        else:
            form = AccountUpdateForm(request.POST,instance=request.user,
                  initial = {
                    "id":account.pk,
                    "email":account.email,
                    "username": account.username,
                    "profile_image": account.profile_image,
                    "hide_email": account.hide_email,
                    "bio":account.bio
                  }
            )
            context['form'] = form
    else:
            form = AccountUpdateForm(
                  initial = {
                    "id":account.pk,
                    "email":account.email,
                    "username": account.username,
                    "profile_image": account.profile_image,
                    "hide_email": account.hide_email,
                    "bio":account.bio
                  }
            )
            context['form'] = form 
    context['DATA_UPLOAD_MAX_MEMORY_SIZE'] = settings.DATA_UPLOAD_MAX_MEMORY_SIZE
    return render(request,'account/edit_account.html',context)
    
def save_temp_profile_image_from_base64String(imageString,user):
    INCORRECT_PADDING_EXCEPTION = "Incorrect padding"
    try:
        if not os.path.exists(settings.TEMP):
            os.mkdir(settings.TEMP)
        if not os.path.exists(f"{settings.TEMP}/{user.pk}"):
            os.mkdir(f"{settings.TEMP}/{user.pk}")
        url = os.path.join(f"{settings.TEMP}\{user.pk}",TEMP_PROFILE_IMAGE_NAME)
        storage = FileSystemStorage(location=url)
        image = base64.b64decode(imageString)
        with storage.open('', 'wb+') as destination:
            destination.write(image)
            destination.close()
        return url
    except Exception as e:
        print(f"exception:{e}")
		# workaround for an issue I found
        if f"{e}" == INCORRECT_PADDING_EXCEPTION:
            imageString += "=" * ((4 - len(imageString) % 4) % 4)
            return save_temp_profile_image_from_base64String(imageString, user)
    return None


    
def crop_image(request, *args, **kwargs):
    payload = {}
    user = request.user
    if request.POST and user.is_authenticated:
        try:
            imageString = request.POST.get("image")
            url = save_temp_profile_image_from_base64String(imageString, user)
            img = cv2.imread(url)

            cropX = int(float(str(request.POST.get("cropX"))))
            cropY = int(float(str(request.POST.get("cropY"))))
            cropWidth = int(float(str(request.POST.get("cropWidth"))))
            cropHeight = int(float(str(request.POST.get("cropHeight"))))
            if cropX <= 0:
                cropX = 0
            if cropY <= 0:
                cropY = 0
            crop_img = img[cropY:cropY+cropHeight, cropX:cropX+cropWidth]

            cv2.imwrite(url, crop_img)

			# delete the old image
            user.profile_image.delete()

			# Save the cropped image to user model
            user.profile_image.save("profile_image.png", files.File(open(url, 'rb')))
            user.save()

            payload['result'] = "success"
            payload['cropped_profile_image'] = user.profile_image.url

			# delete temp file
            os.remove(url)
			
        except Exception as e:
            print(f"exception:{e}")
            payload['result'] = "error"
            payload['exception'] = f"{e}"
    return HttpResponse(json.dumps(payload), content_type="application/json")
