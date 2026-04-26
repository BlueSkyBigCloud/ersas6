from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import UploadedFile, UploadedFileAnalysis
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
import os
from django.core.exceptions import ValidationError
import pandas

def dataupload_view(request):
    if request.method == "POST" and request.FILES.get("file"):
        if not request.user.is_authenticated:
            return redirect('login')  # Redirect to login page if the user is not authenticated

        uploaded_file = request.FILES["file"]

        # Validate file type and size (Example: only CSV files, max size of 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:  # 10 MB limit
            return redirect('upload_file')  # Redirect back if file is too large

        if not uploaded_file.name.endswith('.csv'):
            return redirect('upload_file')  # Redirect back if invalid file type

        # Save the file using FileSystemStorage
        fs = FileSystemStorage(location='/uploads/')
        filename = fs.save(uploaded_file.name, uploaded_file)
        file_url = fs.url(filename)

        # Save the file record in the database
        UploadedFile.objects.create(
            file=file_url,  # Save the file URL
            user=request.user,  # Link file to user
        )

        return redirect('upload_success')  # Redirect to a success page after upload

    return render(request, "dataupload.html")



def analyze_file(uploaded_file):
    """Extract metadata from the uploaded file."""
    file_path = uploaded_file.file.path
    file_size = uploaded_file.file.size
    file_type = os.path.splitext(uploaded_file.file.name)[1].lower()
    
    num_rows = 0
    num_columns = 0
    column_headers = []

    if file_size == 0:
        raise ValidationError("The file is empty.")

    try:
        print(f"Reading file: {file_path}")
        if file_type == ".csv":
            df = pandas.read_csv(file_path)
        elif file_type == ".xlsx":
            df = pandas.read_excel(file_path)
        else:
            raise ValidationError("Unsupported file type.")

        if df.empty:
            raise ValidationError("The file is empty or incorrectly formatted.")

        num_rows = df.shape[0]  # Correctly count the number of rows
        num_columns = df.shape[1]  # Count the number of columns
        column_headers = list(df.columns)

        print(f"DataFrame Shape: {num_rows} rows, {num_columns} columns")
        print(f"Column headers: {column_headers}")
    
    except Exception as e:
        print(f"Error processing file: {e}")
        raise

    return {
        "file_size": file_size,
        "file_type": file_type,
        "num_columns": num_columns,
        "num_rows": num_rows,
        "column_headers": column_headers,
    }


def convert_view(request):
    if request.method == 'POST' and request.FILES['file']:
        uploaded_file = request.FILES['file']
        
        # Step 1: Analyze the file and compare columns with model fields
        analysis_data = analyze_file(uploaded_file, models_to_create)  # Change the model dynamically as needed
        
        # Step 2: Get models that will be created based on the file
        models_to_create = []  # Populate this list based on analysis
        
        # Sample logic to check models for creation (based on analysis_data)
        if 'name' in analysis_data['matching_columns'] and 'address' in analysis_data['matching_columns']:
            models_to_create.append("Location")
        if 'employee_number' in analysis_data['matching_columns']:
            models_to_create.append("Employee")
        if 'category' in analysis_data['matching_columns']:
            models_to_create.append("Equipment")
        if 'service_type' in analysis_data['matching_columns']:
            models_to_create.append("ServiceType")
        if 'service_request' in analysis_data['matching_columns']:
            models_to_create.append("ServiceRequest")

        if 'confirm' in request.POST:  # If user confirms
            # Create the models here based on the columns that match
            for model_name in models_to_create:
                # Example: You would need logic to actually create model instances here
                if model_name == "Location":
                    # Create Location instance
                    pass
                elif model_name == "Employee":
                    # Create Employee instance
                    pass
                # Add logic for other models here
            return render(request, 'success.html', {'message': 'Models created successfully.'})

        return render(request, 'convert_confirm.html', {
            'models_to_create': models_to_create,
            'analysis_data': analysis_data,
        })
    
    return render(request, 'upload_form.html')  # If not POST, show upload form


def convert_file(request, file_id):
    file_instance = get_object_or_404(UploadedFile, id=file_id)
    
    # Perform the conversion (you need to implement this logic based on your needs)
    conversion_result = convert_file_logic(file_instance)  # This should be your actual conversion process.

    return JsonResponse({
        "message": "File converted successfully",
        "conversion_result": conversion_result  # Provide the conversion result here
    })

def convert_file_logic(file_instance):
    # Implement the actual logic for conversion here
    # This might involve parsing the file, transforming data, etc.
    return "Conversion done"  # Example result

def upload_success_view(request):
    return render(request, "upload_success.html")