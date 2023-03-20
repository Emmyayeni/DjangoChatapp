from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from Publicchat.models import PublicChatRoom,Topic
from .forms import RoomForm
from django.conf import settings
# Create your views here.

@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        PublicChatRoom.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        return redirect('home')

    context = {'form': form, 'topics': topics}
    return render(request, 'public/snippets/create_room.html', context)

DEBUG = True

@login_required(login_url='login')
def public_chat(request,pk):
    context = {}
    context['debug_mode'] = settings.DEBUG
    context['debug'] = DEBUG
    context['room_id'] = pk
    public_chat = PublicChatRoom.objects.get(pk=pk)
    context['public_chat'] = public_chat
    

    return render(request,'public/snippets/public_chat.html',context)
