# app1/urls.py

from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('prediction/', views.prediction, name='prediction'),
    path('records/', views.records, name='records'),
    path('about/', views.about, name='about'),
    path('logout/', views.logout, name='logout'),
    path('delete_selected_predictions/', views.delete_selected_predictions, name='delete_selected_predictions'),
    path('download_pdf/', views.download_pdf, name='download_pdf'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('delete_account/', views.delete_account, name='delete_account'),
    path('ai_chat/', views.ai_chat, name='ai_chat'),
    path('ai_chat/sessions/', views.list_chat_sessions, name='list_chat_sessions'),
    path('ai_chat/sessions/<int:session_id>/', views.load_chat_session, name='load_chat_session'),
    path('ai_chat/sessions/<int:session_id>/delete/', views.delete_chat_session, name='delete_chat_session'),
]