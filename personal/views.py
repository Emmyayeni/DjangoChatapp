from django.shortcuts import render

def home_screen(request,*args,**kwargs):
    return render(request,'personal/home.html')

# Create your views here.
