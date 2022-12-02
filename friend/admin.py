from django.contrib import admin

# Register your models here.

from friend.models import FriendList, FriendRequest

class FriendAdmin(admin.ModelAdmin):
    list_filter = ['user']
    list_display = ['user']
    search_fields = ['user']
    
    class Meta:
        model = FriendList
admin.site.register(FriendList,FriendAdmin)


class FriendRequestAdmin(admin.ModelAdmin):
    list_filter = ['sender','receiver']
    list_display = ['sender','receiver']
    search_fields = ['sender__username','sender__email', 'receiver__email','receiver__username']

    class Meta:
        model = FriendRequest
admin.site.register(FriendRequest,FriendRequestAdmin)



