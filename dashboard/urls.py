from django.urls import path
from dashboard import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload, name='upload'),
    path('summaries/', views.summaries, name='summaries'),
    path('gaps/', views.gaps, name='gaps'),
    path('ideas/', views.ideas, name='ideas'),
    path('literature/', views.literature, name='literature'),
    path('experiments/', views.experiments, name='experiments'),
]
