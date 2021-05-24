from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('index/', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),

    # path(r'history/', views.historydata, name='historydata'),
    # path(r'compare/', views.compare, name='compare'),
    # path(r'rank/', views.rank, name='rank'),
    # path(r'^share$', views.share, name='share'),
    # path('gethtml/', views.gethtml),

]
