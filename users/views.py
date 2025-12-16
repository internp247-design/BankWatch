from django.shortcuts import render, redirect
from django.contrib.auth import login, logout  # Add logout import
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm  # Change to custom form
from .models import UserProfile

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'users/home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

# ADD THIS FUNCTION
def custom_logout(request):
    logout(request)
    return redirect('home')

# Add user profile view
def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    user_profile = UserProfile.objects.get(user=request.user)
    context = {
        'user_profile': user_profile
    }
    return render(request, 'users/profile.html', context)