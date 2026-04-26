from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from .forms import *
# Create your views here.


@staff_member_required
def upload_apk(request):
    if request.method == 'POST':
        form = APKUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # Save the file to MongoDB
            return redirect('apk_list')  # Redirect to a page where APKs can be downloaded
    else:
        form = APKUploadForm()
    return render(request, 'upload_apk.html', {'form': form})