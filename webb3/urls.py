from django.urls import path
from . import views


urlpatterns=[
    path("Signout/", views.Signout, name="Signout"),
    path("Login/", views.login, name="login"),
    path("first/",views.first,name="first"),
     path("Members/",views.members,name="members"),
     path("Workgroup/",views.workgroup,name="workgroup"),
      path('workgroup/data/', views.workgroup_data, name='workgroup_data'),
    ]