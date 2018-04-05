from django import forms
from online_classes.models import userInfo, emailInfo, userProfileSettings
from django.forms import ModelForm

class profileSettings(forms.ModelForm):
    countryField = forms.CharField()
    stateField = forms.CharField()
    cityField = forms.CharField()
    class Meta:
        model = userProfileSettings
        fields = ['firstname', 'lastname', 'gender', 'dateofbirth', 'countryField', 'stateField', 'cityField']


class EmailValidateForm(forms.ModelForm):
    name = forms.EmailField(widget=forms.TextInput)
    class Meta:
        model = emailInfo
        fields = ['name']

class LoginForm(forms.ModelForm):
    class Meta:
        model = userInfo
        fields = ['password']

class ProfileImage(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ProfileImage, self).__init__(*args, **kwargs)
        self.fields['image'].required = True

    class Meta:
        model = userInfo
        fields = ['image']
