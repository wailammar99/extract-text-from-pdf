from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login ,authenticate
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.models import User
from .models import *
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from PyPDF2 import PdfReader
import os
import fitz  # PyMuPDF
# PyMuPDF
from django.conf import settings
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('home')  # Redirect to the home page after login
        else:
            return HttpResponse('Invalid credentials', status=401)  # Handle invalid login attempts

    return render(request, 'html/login.html')
# Render a template named 'login.html'
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Simple validation
        if not username or not email or not password1 or not password2:
            messages.error(request, 'All fields are required.')
            return render(request, 'html/register.html')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'html/register.html')
        
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Invalid email address.')
            return render(request, 'html/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'html/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered.')
            return render(request, 'html/register.html')

        # Create the user
        user = User.objects.create_user(username=username, email=email, password=password1,is_superuser=False)
          # Automatically log in the user after registration
        return redirect('login')  # Redirect to a home page or another page after registration

    return render(request, 'html/register.html')
@login_required
def home_view(request):
    return render(request, 'html/home.html')

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return redirect('home')  # Handle GET requests if needed
@login_required
@csrf_exempt

def upload_pdf_view(request):
    if request.method == 'POST':
        if 'pdf_file' not in request.FILES:
            return JsonResponse({'message': 'No file uploaded.'}, status=400)

        pdf_file = request.FILES['pdf_file']
        user = request.user
        max_file_size = 10 * 1024 * 1024  # 10 MB

        if pdf_file.size > max_file_size:
            return JsonResponse({'message': 'File size exceeds 10 MB limit.'}, status=400)
        
        # Define the local directory to save uploaded files
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)  # Create directory if it doesn't exist

        # Save the file to the local directory
        file_path = os.path.join(upload_dir, pdf_file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in pdf_file.chunks():
                destination.write(chunk)

        # Initialize variables for text extraction and image URLs
        image_urls = []
        text = ""

        try:
            # Open the saved PDF file
            pdf_document = fitz.open(file_path)
            
            # Extract text from all pages
            for page_num in range(len(pdf_document)):  # Iterate through pages
                page = pdf_document.load_page(page_num)
                page_text = page.get_text()
                if page_text:
                    text += page_text
            
            # Render and save images from the first three pages
            for page_num in range(min(3, len(pdf_document))):  # Process up to 3 pages
                page = pdf_document.load_page(page_num)
                pix = page.get_pixmap()  # Render page to an image (pixmap)
                # Generate a unique filename with timestamp and page number
                timestamp = now().strftime('%Y%m%d%H%M%S')
                image_filename = f"page_{page_num + 1}_{timestamp}.png"
                image_path = os.path.join(upload_dir, image_filename)
                pix.save(image_path)  # Save the image file
                image_urls.append(os.path.join(settings.MEDIA_URL, 'uploads', image_filename))

        except Exception as e:
            print(f"Error: {str(e)}")  # Debug statement
            return JsonResponse({'message': f"Error processing PDF: {str(e)}"}, status=500)

        # Save PDF and extracted text and images to database
        uploaded_pdf = UploadedPDF.objects.create(
            user=user,
            pdf_file=os.path.join('uploads', pdf_file.name),  # Save relative path in the model
            text=text,
            image_urls=image_urls
        )

        print(f"Image URLs: {image_urls}")  # Debug statement

        return JsonResponse({
            'message': 'PDF uploaded and text extracted successfully!',
            'image_urls': image_urls
        }, status=200)
    
    return JsonResponse({'message': 'Invalid request method.'}, status=405)
@login_required
def profil(request):
    user = request.user
    
    if request.method == 'POST':
        # Update user profile information
        username = request.POST.get('name')
        email = request.POST.get('email')
        first_name = request.POST.get('prenom')
        last_name = request.POST.get('last_name')

        if username:
            user.username = username
        if email:
            user.email = email
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        
        user.save()

        # Return a JSON response to the frontend
        return JsonResponse({'message': 'Profile updated successfully!'})

    # For GET requests, just render the profile page with current user data
    return render(request, "html/profil.html", {'user': user})

@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')

        # Verify the current password
        if not request.user.check_password(current_password):
            return JsonResponse({'message': 'Current password is incorrect.'}, status=400)

        # Update the password
        user = request.user
        user.set_password(new_password)
        user.save()

        # Log the user out and prompt to log back in
        
        logout(request)

        return JsonResponse({'message': 'Password updated successfully!'})
    
    return JsonResponse({'message': 'Invalid request method.'}, status=405)
def user_uploaded_pdfs_view(request):
    uploaded_pdfs = UploadedPDF.objects.filter(user=request.user)
    context = {'uploaded_pdfs': uploaded_pdfs}
    return render(request, 'html/user_uploaded_pdfs.html', context)
def pdf_detail_view(request, pdf_id):
    pdf = get_object_or_404(UploadedPDF, id=pdf_id, user=request.user)
    context = {
        'pdf': pdf,
    }
    return render(request, 'pdf_detail.html', context)
def pdf_list_view(request):
    uploaded_pdfs = UploadedPDF.objects.all()
    
    # Create a dictionary to map each PDF to its related images
    pdf_images = {}
    for pdf in uploaded_pdfs:
        # Assuming each PDF has a ForeignKey or a relationship to ImageModel
        images = ImageModel.objects.filter(pdf=pdf)
        pdf_images[pdf.id] = images
    
    context = {
        'uploaded_pdfs': uploaded_pdfs,
        'pdf_images': pdf_images,
    }
    return render(request, 'your_template.html', context)