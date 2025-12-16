from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    date_of_birth = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    city = forms.CharField(max_length=100, required=False)
    country = forms.CharField(max_length=100, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'phone_number', 
                  'date_of_birth', 'address', 'city', 'country')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Save additional profile data
            user_profile = user.userprofile
            user_profile.phone_number = self.cleaned_data['phone_number']
            user_profile.date_of_birth = self.cleaned_data['date_of_birth']
            user_profile.address = self.cleaned_data['address']
            user_profile.city = self.cleaned_data['city']
            user_profile.country = self.cleaned_data['country']
            user_profile.save()
        
        return user