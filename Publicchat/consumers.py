from django.core.serializers.python import Serializer
from django.core.paginator import Paginator
from django.core.serializers import serialize
from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from chat.exception import ClientError
from chat.utils import calculate_timestamp
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from django.contrib.humanize.templatetags.humanize import naturalday,naturaltime
from django.utils import timezone
from datetime import datetime
from Publicchat.models import PublicChatRoom,PublicRoomChatMessage
from Publicchat.constant import DEFAULT_ROOM_CHAT_MESSAGE_PAGE_SIZE, MSG_TYPE_MESSAGE, MSG_TYPE_CONNECTED_USER_COUNT
User = get_user_model()
from asgiref.sync import sync_to_async

class PublicChatConsumer(AsyncJsonWebsocketConsumer):
    	
	async def connect(self):
		"""
			Called when the websocket is handshaking as part of initial connection
		"""
		print(f"PublicChatConsumer: connect {self.scope['user']}")
			
		await self.accept()


		self.room_id = None
			
	async def disconnect(self, code):
		"""
		Called when the WebSocket closes for any reason.
		"""
		# leave the room
		print("PublicChatConsumer: disconnect")
		try:
			if self.room_id != None:
				await self.leave_room(self.room_id)
		except Exception:
			pass

	async def receive_json(self, content):
		"""
		Called when we get a text frame. Channels will JSON-decode the payload
		for us and pass it as the first argument.
		"""
		# Messages will have a "command" key we can switch on
		command = content.get("command", None)
		print("PublicChatConsumer: receive_json: " + str(command))
		try:
			if command == "send":
				if len(content["message"].lstrip()) != 0:
					await self.send_room(content["room_id"], content["message"])
					# raise ClientError(422,"You can't send an empty message.")
			elif command == "join":
				# Make them join the room
				await self.join_room(content["room"])
				await add_participant(content['room'],self.scope['user'])
			elif command == "leave":
				# Leave the room
				await self.leave_room(content["room"])
			elif command == "get_room_chat_messages":
				await self.display_progress_bar(True)
				room = await get_room_or_error(content['room_id']) 
				payload = await get_room_chat_message(room, content['page_number'])
				if payload !=None:
					payload = json.loads(payload)
					await self.send_messages_payload(payload["message"],payload['new_page_number'])
				else:
					raise ClientError(204,"something went wrong retrieving chatroom messages.")
				await self.display_progress_bar(False)
			elif command == "user_msg_type":
				await self.connected_user_count()
		except ClientError as e:
			await self.display_progress_bar(False)
			await self.handle_client_error(e)

	async def send_message(self,message):
			await self.channel_layer.group_send(
				"public_chatroom_1",
				{
					"type":"chat.message",# chat_message
			 		"profile_image": self.scope['user'].profile_image.url,
					"username": self.scope['user'].username,
					"user_id": self.scope['user'].id,
					"message": message,

				}
			)
		
		
	async def send_room(self,room_id,message):
		"""
			Called by receive_json when someone sends a message to a room 
		"""
		print("PublicChatConsumer:send_room")
		if self.room_id !=None:
			if str(room_id) != str(self.room_id):
				raise ClientError("ROOM_ACCESS_DENIED","room access denied ")
			if not is_authenticated(self.scope['user']):
				raise ClientError("AUTH_ERROR","you nust be authenticted to chat")
		else:
			raise ClientError("ROOM_ACCESS_DENIED","Room access denied")		
		room = await get_room_or_error(room_id)
		await create_public_room_chat_message(room,self.scope['user'],message)
		await self.channel_layer.group_send(
			room.group_name,
			{
				"type":"chat.message",# chat_message
				"profile_image": self.scope['user'].profile_image.url,
				"username": self.scope['user'].username,
				"user_id": self.scope['user'].id,
				"message": message,
			}
		)

	async def chat_message(self,event):
		""" 
		Called when someone has messaged our chat 
		"""
		# send a messagae down to the client
		print(f"PublicChatConsumer: chat_message from user #: {event['user_id']}")
		timestamp = calculate_timestamp(timezone.now())
		await self.send_json({
			"msg_type":MSG_TYPE_MESSAGE, 
			"profile_image":event['profile_image'],
			"username":event['username'],
			"user_id":event['user_id'],
			"message":event['message'],
			"natural_timestamp":timestamp
		})

	async def join_room(self, room_id):
		"""
		Called by receive_json when someone sent a join command.
		"""
		print("PublicChatConsumer: join_room")
		is_auth = is_authenticated(self.scope["user"])
		try:
			room = await get_room_or_error(room_id)
		except ClientError as e:
			await self.handle_client_error(e)
		# Add user to "users" list for room
		# if is_auth:
		# await connect_user(room, self.scope["user"])

		# Store that we're in the room
		self.room_id = room.id

		# Add them to the group so they get room messages
		await self.channel_layer.group_add(
			room.group_name,
			self.channel_name,
		)

		# Instruct their client to finish opening the room
		await self.send_json({
			"join": str(room.id),
			"username": str(self.scope['user'].username)
		})

		# num_connected_users = get_num_connected_users(room)
		# await self.channel_layer.group_send(
		# 	room.group_name,
		# 	{
		# 		"type": "connected.user.count",
		# 		"connected_user_count": num_connected_users,
		# 	}
		# )

	async def leave_room(self,room_id):
		"""
			CAlled by receive_json when someone sent a leave command
		"""
		print("publicChatConsumer: leave_room")
		is_auth = is_authenticated(self.scope['user'])
		try:
			room = await get_room_or_error(room_id)
		except ClientError as e:
			await self.handle_client_error(e)
		# Remove user from "user list"
		# if is_auth:
		# 	await disconnect_user(room,self.scope['user'])
		# # Remove that we're in the room
		self.room_id = None

		# send the new user count to the room
		
		# Remove them from the group so they no longer receive messages 
		await self.channel_layer.group_discard(
			room.group_name,
			self.channel_name
		)
	async def send_messages_payload(self,messages,new_page_number):
		"""
			sends a payloads of mesages to the UI
		"""
		print("PublicchatConsumer:send_messages_payload.")
		await self.send_json({
			"messages_payload": "messages_payload",
			"messages":messages,
			"new_page_number": new_page_number,
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
		
	async def connected_user_count(self, event):
		"""
		Called to send the number of connected users to the room.
		This number is displayed in the room so other users know how many users are connected to the chat.
		"""
		# Send a message down to the client
		print("PublicChatConsumer: connected_user_count: count: " + str(event["connected_user_count"]))
		await self.send_json(
			{
				"msg_type": MSG_TYPE_CONNECTED_USER_COUNT,
				"connected_user_count": event["connected_user_count"]
			},
		)



async def is_authenticated(user):
	if user.is_authenticated:
		return  True
	return False


def get_num_connected_users(room):
	if room.users:
		return str(len(room.users.all()))
	return str(0)


@database_sync_to_async
def create_public_room_chat_message(room, user, message):
    	return PublicRoomChatMessage.objects.create(user=user,room=room,content=message)

# @database_sync_to_async
# def connect_user(room,user):
#     return room.connect_user(user)

# @database_sync_to_async
# def disconnect_user(room,user):
#     	return room.disconnect_user(user)

@database_sync_to_async 
def get_room_or_error(room_id):
	"""
	Tries to fetch a room for the user 
	"""
	try:
		room = PublicChatRoom.objects.get(pk=room_id)
	except: 
		raise ClientError("ROOM_INVALID", "Invalid room")
	return room



@database_sync_to_async
def add_participant(room_id,user):
    try:   
        room = PublicChatRoom.objects.get(pk=room_id)
        PublicChatRoom.add_user(room,user)
    except PublicChatRoom.DoesNotExist:
       print('room does not exist')


@database_sync_to_async
def get_room_chat_message(room, page_number):
	try:
		qs = PublicRoomChatMessage.objects.by_room(room)
		p = Paginator(qs,DEFAULT_ROOM_CHAT_MESSAGE_PAGE_SIZE)

		payload ={}
		new_page_number = int(page_number)
		if new_page_number <= p.num_pages:
				new_page_number = new_page_number + 1
				s = LazyRoomChatMessageEncoder()
				payload['message'] =s.serialize(p.page(page_number).object_list)
		else:
			payload['message'] = "None"
		payload["new_page_number"] = new_page_number
		return json.dumps(payload)
	except Exception as e:
		print(f"ExCEPTION: {e}")
		return None

class LazyRoomChatMessageEncoder(Serializer):
	def get_dump_object(self,obj):
		dump_object = {}
		dump_object.update({'msg_type': MSG_TYPE_MESSAGE})
		dump_object.update({'user_id': str(obj.user.id)})
		dump_object.update({'msg_id': str(obj.id)})
		dump_object.update({'username': str(obj.user.username)})
		dump_object.update({'message': str(obj.content)})
		dump_object.update({'profile_image': str(obj.user.profile_image.url)})
		dump_object.update({'natural_timestamp':calculate_timestamp(obj.timestamp)}) 

		return dump_object  