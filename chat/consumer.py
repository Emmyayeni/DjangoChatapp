from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.serializers import serialize
from django.utils import timezone
from django.core.paginator import Paginator
from chat.utils import caculate_timestamp,LazyRoomChatMessageEncoder
from chat.exception import ClientError
from chat.constants import *
import json
import asyncio
from chat.models import RoomChatMessage, PrivateChatRoom
from friend.models import FriendList
from account.models import Account
from account.utils import LazyAccountEncoder

class ChatConsumer(AsyncJsonWebsocketConsumer):


	async def connect(self):
		"""
		Called when the websocket is handshaking as part of initial connection.
		"""
		print("ChatConsumer: connect: " + str(self.scope["user"]))

		# let everyone connect. But limit read/write to authenticated users
		await self.accept()

		# the room_id will define what it means to be "connected". If it is not None, then the user is connected.
		self.room_id = None


	async def receive_json(self, content):
		"""
		Called when we get a text frame. Channels will JSON-decode the payload
		for us and pass it as the first argument.
		"""
		# Messages will have a "command" key we can switch on
		print("ChatConsumer: receive_json")
		command = content.get("command", None)
		try:
			if command == "join":
				print("joining room: " + str(content['room']))
				await self.join_room(content['room'])

			elif command == "leave":
				# Leave the room
				pass
			elif command == "send":
				if len(content['message'].lstrip()) == 0:
					raise ClientError(422,"You can't send an empty message.")
				await self.send_room(content['room'],content['message'])
			elif command == "get_room_chat_messages":
				await self.display_progress_bar(True)
				room = await get_room_or_error(content['room_id'],self.scope['user'])
				print(room)
				payload = await get_room_chat_messages(room, content['page_number'])
				if payload != None:
					payload = json.loads(payload)
					await self.send_messages_payload(payload['messages'],payload['new_page_number'])
				else:
					raise ClientError(204, "something went wrong while retrieving the chatrom messages.")
				self.display_progress_bar(False)
			elif command == "get_user_info":
				await self.display_progress_bar(True)
				room = await get_room_or_error(content['room_id'], self.scope['user'])
				payload = get_user_info(room, self.scope['user'])
				if payload != None:
					payload = json.loads(payload)
					await self.send_user_info_payload(payload['user_info'])
					print('yh i got the info')
				else:
					self.display_progress_bar(False)
					print('something went wrong')
					raise ClientError("SOMETHING_WENT_WRONG","something went wrong retrieving the other user account info")
				self.display_progress_bar(False)	
		except ClientError as e:
			await self.display_progress_bar(False)
			await self.handle_client_error(e)

	async def disconnect(self, code):
		"""
		Called when the WebSocket closes for any reason.
		"""
		# Leave the room
		print("ChatConsumer: disconnect")


	async def join_room(self, room_id):
		"""
		Called by receive_json when someone sent a join command.
		"""
		# The logged-in user is in our scope thanks to the authentication ASGI middleware (AuthMiddlewareStack)
		print("ChatConsumer: join_room: " + str(room_id))
		try:
			room = await get_room_or_error(room_id, self.scope['user'])
			print("got room")
		except ClientError as e :
			return await self.handle_client_error(e)
		# STORE THAT WE ARE IN THE ROOM
		self.room_id = room.id
		await self.channel_layer.group_add(
			room.group_name,
			self.channel_name
		)
		await self.send_json({
			"join": str(room.id)
		})
		if self.scope['user'].is_authenticated:
				await self.channel_layer.group_send(
					room.group_name,
					{
						"type":"chat.join",
						"room_id":room_id,
						"profile_image": self.scope['user'].profile_image.url,
						"username": self.scope['user'].username,
						"user_id": self.scope['user'].id,
					}
				)
			
	async def leave_room(self, room_id):
		"""
		Called by receive_json when someone sent a leave command.
		"""
		# The logged-in user is in our scope thanks to the authentication ASGI middleware
		print("ChatConsumer: leave_room")
		room = await get_room_or_error(room_id,self.scope['user'])

		await self.channel_layer.group_send(
			room.group_name,
			{
			"type":"chat.leave", 
			"room_id": room_id,
			"profile_image": self.scope['user'].profile_image.url,
			"user_id": self.scope['user'].id
			}
		)
		self.room_id=None
		# Removee the from the group so they n longer get room message
		
		await self.channel_layer.group_discard({
			room.group_name,
			self.channel_name
		})

		await self.send_json({
			"leave": str(room.id)
		})

	async def send_room(self, room_id, message):
		"""
		Called by receive_json when someone sends a message to a room.
		"""
		print("ChatConsumer: send_room")
		# Check they are in this room
		if self.room_id != None:
			if str(room_id) != str(self.room_id):
				raise ClientError('ROOM_ACESS_DENIED',"room acesss denied")
		else:
			raise ClientError('ROOM_ACESS_DENIED',"room acesss denied")
		
		room = 	await get_room_or_error(room_id,self.scope['user'])
		await create_room_chat_message(room, self.scope['user'], message)
		await self.channel_layer.group_send(
			room.group_name,
			{
			
				"type": "chat.message",
				"profile_image": self.scope['user'].profile_image.url,
				"username": self.scope["user"].username,
				"user_id": self.scope["user"].id,
				"message": message,
			
			}
		)

	# These helper methods are named by the types we send - so chat.join becomes chat_join
	async def chat_join(self, event):
		"""
		Called when someone has joined our chat.
		"""
		# Send  a message down to the client
		print("ChatConsumer: chat_join: " + str(self.scope["user"].id))
		if event['username']:
			await self.send_json({
				"msg_type": MSG_TYPE_ENTER,
				"room":event['room_id'],
				"profile_image": event['profile_image'],
				"username": event['username'],
				"user_id": event['user_id'],
				"message": event['username'] + "connected.",
			}) 
	async def chat_leave(self, event):
		"""
		Called when someone has left our chat.
		"""
		# Send a message down to the client
		print("ChatConsumer: chat_leave")
		if event['username']:
				await self.send_json({
				"msg_type": MSG_TYPE_LEAVE ,
				"room":event['room_id'],
				"profile_image": event['profile_image'],
				"username": event['username'],
				"user_id": event['user_id'],
				"message":event['message'] + "disconnected.",
			})

	async def chat_message(self, event):
		"""
		Called when someone has messaged our chat.
		"""
		# Send a message down to the client
		print("ChatConsumer: chat_message")

		timestamp = caculate_timestamp(timezone.now())

		await self.send_json({
			'msg_type': MSG_TYPE_MESSAGE,
			'username':event['username'],
			'user_id':event['user_id'],
			'profile_image':event['profile_image'],
			"message": event["message"],
			'natural_timestamp':timestamp,
		})

	async def send_messages_payload(self, messages, new_page_number):
		"""
		Send a payload of messages to the ui
		"""
		print("ChatConsumer: send_messages_payload. ")
		await self.send_json({
			"messages_payload": "messages_payload",
			"messages":messages,
			"new_page_number": new_page_number

		})

	async def send_user_info_payload(self, user_info):
		"""
		Send a payload of user information to the ui
		"""
		print("ChatConsumer: send_user_info_payload. ")
		await self.send_json({
			"user_info": user_info
		})

	async def handle_client_error(self,e):
		""" 
		Called when  a ClientError is rated.
		sends error data to the UI 
		"""
		errorData = {}
		errorData['error'] = e.code
		if e.message:
			errorData["message"] = e.message
		await self.send_json(errorData)

	async def display_progress_bar(self,is_displayed):
		print("DISPLAY PROGRESS BAR: " + str(is_displayed))
		await self.send_json({
			"display_progress_bar": is_displayed
		}) 
		
@database_sync_to_async
def get_room_or_error(room_id,user):
    """
        Tries to fetch a room for the user, checking permission along the way.
    """
    try:
        room = PrivateChatRoom.objects.get(pk=room_id)
    except PrivateChatRoom.DoesNotExist:
        raise ClientError("INVALID_ROOM","Invalid room.")

    if user != room.user1 and user !=room.user2:
        raise ClientError("you are not allowed to join this room")
    #Is this is user allowed into this room?
    friend_list = FriendList.objects.get(user=user).friends.all()
    if not room.user1 in friend_list:
        if not room.user2 in friend_list:
           raise ClientError("ACCESS_DENIED","you must be friend to chat.") 
    return room
    


def get_user_info(room, user):
    """
        Retrieve the user for the user you are chatting with.

    """
    try:
        #Determine who is who 
        
        if room.user1 == user:
            other_user = room.user2 
        elif room.user2 == user:
          other_user = room.user1 
    			
        payload ={}
        s = LazyAccountEncoder()
        payload['user_info'] = s.serialize([other_user])[0]
       
        print(payload['user_info'])
        return json.dumps(payload)   
    
    except ClientError as e:
        print("EXCEPTION:" +str(e))
    
    return None


@database_sync_to_async
def create_room_chat_message(room,user,message):
    	return RoomChatMessage.objects.create(user=user,room=room,content=message)

@database_sync_to_async
def get_room_chat_messages(room, page_number):
	try:
		qs = RoomChatMessage.objects.by_room(room)
		p = Paginator(qs,DEFAULT_ROOM_CHAT_MESSAGE_PAGE_SIZE)
		payload ={}
		new_page_number = int(page_number)
		if new_page_number <= p.num_pages:
			new_page_number = new_page_number + 1
			s = LazyRoomChatMessageEncoder()
			payload['messages'] = s.serialize(p.page(page_number).object_list)
		else:
			payload['messages'] = "None"
		payload['new_page_number'] = new_page_number
		return json.dumps(payload)
	except Exception as e:
		print("EXCEPTION:" + str(e))
	return None

