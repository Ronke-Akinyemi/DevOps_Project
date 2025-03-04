from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.UserProfileView.as_view(), name='home'),
    path('is_subscribed/', views.UserIsSubscribe.as_view(), name='is_subscribe'),
    path("plans/", views.ListAllPlansViews.as_view(),name="list_plans"),
    path("subscribe/", views.UserSubscribeView.as_view(), name="subscribe"),
    path("active_plan/", views.UserActivePlan.as_view(), name="active_plan"),
]