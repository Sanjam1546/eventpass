from django.urls import path
from . import views

app_name = 'passes'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('events/', views.event_list, name='event_list'),
    path('events/create/', views.event_create, name='event_create'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('events/<int:event_id>/sessions/create/', views.session_create, name='session_create'),
    path('events/<int:event_id>/register/', views.register_pass, name='register_pass'),

    path('events/<int:event_id>/members/', views.member_list, name='member_list'),
    path('sessions/<int:session_id>/members/add/', views.member_create, name='member_create'),
    path('members/<int:pk>/pass/', views.member_pass_detail, name='member_pass_detail'),

    path('my-passes/', views.my_passes, name='my_passes'),
    path('my-passes/<int:pk>/', views.pass_detail, name='pass_detail'),

    path('scanner/', views.scanner_view, name='scanner'),
    path('scanner/scan/', views.scan_api, name='scan_api'),
]
