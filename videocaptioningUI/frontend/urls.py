from django.urls import path
from .views import VideoCaptionView

urlpatterns = [
    path("", VideoCaptionView.as_view(), name="home_view")
]