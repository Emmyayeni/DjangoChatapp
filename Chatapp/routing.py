from django.urls import path
from Publicchat.consumers import PublicChatConsumer
from chat.consumer import ChatConsumer
from notification.consumer import NotificationConsumer

ws_urlpatterns = [
	path('Publicchat/<room_id>/',PublicChatConsumer.as_asgi()),
	path('chat/<room_id>',ChatConsumer.as_asgi()),
	path('',NotificationConsumer.as_asgi()),
]
