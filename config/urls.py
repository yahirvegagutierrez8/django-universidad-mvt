from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from academico.views import LoginConMensajeView, RegistroView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", LoginConMensajeView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("registro/", RegistroView.as_view(), name="registro"),
    path("", include("academico.urls")),
]
