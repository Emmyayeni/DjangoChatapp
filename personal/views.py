from django.shortcuts import render,redirect
from django.conf import settings
from Publicchat.forms import RoomForm
from account.models import Account,FriendList
DEBUG = False
from django.contrib.auth.decorators import login_required
from Publicchat.models import PublicChatRoom,Topic
from django.core.paginator import Paginator


@login_required(login_url='login')
def home_screen(request):
    context = {}
    public_room = PublicChatRoom.objects.all()
    paginator = Paginator(public_room,5)
    page = request.GET.get('page')
    room_list = paginator.get_page(page)
    users = Account.objects.all()
    friendlist = FriendList.objects.get(user=request.user)
    other_user = []
    for user in users:
        if user not in friendlist.friends.all() and user!= request.user:
            other_user.append(user)
            print(other_user)

    everychat = public_room.count()
    topic = Topic.objects.all()
    print(public_room)
    context['public_room'] = room_list
    context['topics'] = topic
    context['everychat'] = everychat
    context['acts']  = other_user

    return render(request,'personal/home.html',context)
    

# Create your views here.

