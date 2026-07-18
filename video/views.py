from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from app.decorators import onboarded
from .models import Video
from app.models import Company

@login_required
@onboarded()
def video_view(request):
    user_company = getattr(request.user, 'company', None) 
    videos = Video.objects.filter(company=user_company) if user_company else Video.objects.none()

    return render(request, 'video_view.html', {'videos': videos})