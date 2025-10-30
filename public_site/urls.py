from django.urls import path
from . import views
from public_site import views 

# --- Public Site URLs ---
    # path('', public_views.home_page, name='home'),
    # for now public_site app prifix will be 'home'
urlpatterns = [
    path('', views.home_page, name='home'),
    
    # Add this new URL for logging out from the homepage
    path('logout/', views.public_logout_view, name='public-logout'),
    # path('about/', public_views.about_page, name='about'),
]

