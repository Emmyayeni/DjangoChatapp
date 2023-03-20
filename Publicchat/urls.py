from django.urls import path,include
from Publicchat.views import (
    createRoom,
    public_chat
    
)
app_name = 'public'
urlpatterns = [
    path('create-room',createRoom,name='create-room'),
    path('room/<str:pk>/',public_chat, name="room"),
]

