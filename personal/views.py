from django.shortcuts import render,redirect
from django.conf import settings

DEBUG = False

def public_chat(request,*args,**kwargs):
    context = {}
    context['debug_mode'] = settings.DEBUG
    context['debug'] = DEBUG
    context['room_id'] = 1
    return render(request,'public/snippets/public_chat.html',context)

def home_screen(request):
    return render(request,'personal/home.html')

# Create your views here.

