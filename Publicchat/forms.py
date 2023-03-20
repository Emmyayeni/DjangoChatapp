from django.forms import ModelForm
from .models import PublicChatRoom

class RoomForm(ModelForm):
    class Meta:
        model = PublicChatRoom
        fields = '__all__'
        exclude = ['host', 'participants']
