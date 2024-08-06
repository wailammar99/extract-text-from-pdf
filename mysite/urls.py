from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views  # Import views from the current app

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('home/', views.home_view, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('upload_pdf/', views.upload_pdf_view, name='upload_pdf'),
    path('profil/', views.profil, name='profil'),
    path('change_password/', views.change_password, name='change_password'),
    path("mypdf",views.user_uploaded_pdfs_view,name="pdf/user"),
    path('pdf/<int:pdf_id>/', views.pdf_detail_view, name='pdf_detail'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
