from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from app.decorators import onboarded
from .models import Video


@login_required
@onboarded()
def video_view(request):
    videos = Video.objects.all()
    return render(request, 'video_view.html', {'videos': videos})