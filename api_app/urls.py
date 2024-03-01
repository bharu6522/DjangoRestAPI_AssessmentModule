from urllib import request
from django.urls import path
from . import views
from .views import get_answer


urlpatterns = [
    # path('<str:user_name>/<str:assessment_name>/', views.user_login, name='user_login'),
    
   path('create/<str:user_name>/<str:assessment_name>/',views.get_or_create_assessment_session, name='create_session'),
    
    path('<str:user_name>/<str:assessment_name>/myanswer/<str:user_answers>/<str:operation>/<str:serial_no>/', views.get_answer ,name='get_answer'),
   
    path('create/<str:industry_name>/<str:user_name>/<str:assessment_name>/',views.industry_get_or_create_assessment_session, name='create_session'),
    
    path('<str:industry_name>/<str:user_name>/<str:assessment_name>/myanswer/<str:user_answers>/<str:operation>/<str:serial_no>/', views.industry_get_answer ,name='get_answer'),
   
   
]
