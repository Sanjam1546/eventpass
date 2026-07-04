from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.EventPassLoginView.as_view(), name='login'),
    path('register/', views.SignUpView.as_view(), name='register'),
    path('logout/', views.logout_view, name='logout'),
]
