from django.contrib.auth import views as auth_views
from django.urls import path

from diary import views

app_name = 'diary'

urlpatterns = [
    path('', views.EntryListView.as_view(), name='entry_list'),
    path('entry/<int:pk>/', views.EntryDetailView.as_view(), name='entry_detail'),
    path('entry/create/', views.EntryCreateView.as_view(), name='entry_create'),
    path('entry/<int:pk>/edit/', views.EntryUpdateView.as_view(), name='entry_update'),
    path('entry/<int:pk>/delete/', views.EntryDeleteView.as_view(), name='entry_delete'),

    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
