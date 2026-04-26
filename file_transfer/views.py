from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from app.decorators import onboarded
from django.db import models
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from .models import *
from django.db import models
from users.models import CustomUser
from django.http import HttpResponse, Http404


@onboarded()
@login_required
def file_transfer_list(request):
    # Get all FileTransfer objects related to the current user (either as 'from_user' or 'to_user')
    file_transfers = FileTransfer.objects.filter(
        models.Q(from_user=request.user) | models.Q(to_user=request.user)
    ).order_by('-timestamp')  # Order by timestamp, most recent first

    # Render the file transfers to the template
    return render(request, "file_transfer_list.html", {"file_transfers": file_transfers})

MAX_FILE_SIZE = 1000 * 1024 * 1024  # 10 MB limit, adjust as needed


@onboarded()
@login_required
def file_transfer(request):
    company = request.user.company
    if request.method == "POST":
        file = request.FILES.get("file")
        to_user_id = request.POST.get("to_user")

        if file:
            # Validate file type
            allowed_extensions = ['csv', 'dat', 'jpg', 'mp3', 'mp4']
            if file.name.split('.')[-1].lower() not in allowed_extensions:
                return HttpResponse("Only .csv, .dat, and .jpg files are supported.")

            # Validate file size
            if file.size > MAX_FILE_SIZE:
                return HttpResponse(f"File size exceeds the {MAX_FILE_SIZE // (1024 * 1024)}MB limit.")

            # Retrieve recipient user
            try:
                to_user = CustomUser.objects.get(id=to_user_id, company=request.user.company)
            except CustomUser.DoesNotExist:
                return HttpResponse("Recipient user does not exist.")

            # Generate unique filename
            file_uuid = f"{uuid.uuid4()}.{file.name.split('.')[-1]}"
            fs = FileSystemStorage()
            filename = fs.save(file_uuid, file)

            # Save the file transfer record
            file_transfer = FileTransfer.objects.create(
                file=filename, from_user=request.user, to_user=to_user
            )
            return redirect("file_transfer")

    # Get users in the same company for the dropdown
    users_in_company = company.customusers.all()
    return render(request, "file_transfer.html", {"users": users_in_company})



@login_required
def download_file(request, file_id):
    try:
        file_transfer = FileTransfer.objects.get(id=file_id, to_user=request.user)
        
        # Mark as opened if it is not opened
        if not file_transfer.opened:
            file_transfer.mark_as_opened()

        # Check for expiration
        if file_transfer.is_expired():
            file_transfer.delete_file()
            return HttpResponse("The file link has expired.", status=410)  # 410 Gone for expired files
        
        # Get the file path and serve the file
        file_path = os.path.join(settings.MEDIA_ROOT, file_transfer.file.name)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                response = HttpResponse(f.read(), content_type="application/octet-stream")
                response["Content-Disposition"] = f"attachment; filename={os.path.basename(file_path)}"
                return response
        else:
            raise Http404("File not found.")
    except FileTransfer.DoesNotExist:
        raise Http404("File not available.")
    