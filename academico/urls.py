from django.urls import path

from . import views

app_name = "academico"

urlpatterns = [
    path("", views.InicioView.as_view(), name="inicio"),
    # Cursos
    path("cursos/", views.CursoListView.as_view(), name="curso_list"),
    path("cursos/nuevo/", views.CursoCreateView.as_view(), name="curso_create"),
    path("cursos/<int:pk>/", views.CursoDetailView.as_view(), name="curso_detail"),
    path(
        "cursos/<int:pk>/editar/",
        views.CursoUpdateView.as_view(),
        name="curso_update",
    ),
    path(
        "cursos/<int:pk>/eliminar/",
        views.CursoDeleteView.as_view(),
        name="curso_delete",
    ),
    # Profesores
    path("profesores/", views.ProfesorListView.as_view(), name="profesor_list"),
    path(
        "profesores/nuevo/",
        views.ProfesorCreateView.as_view(),
        name="profesor_create",
    ),
    path(
        "profesores/<int:pk>/",
        views.ProfesorDetailView.as_view(),
        name="profesor_detail",
    ),
    path(
        "profesores/<int:pk>/editar/",
        views.ProfesorUpdateView.as_view(),
        name="profesor_update",
    ),
    path(
        "profesores/<int:pk>/eliminar/",
        views.ProfesorDeleteView.as_view(),
        name="profesor_delete",
    ),
    # Estudiantes
    path("estudiantes/", views.EstudianteListView.as_view(), name="estudiante_list"),
    path(
        "estudiantes/nuevo/",
        views.EstudianteCreateView.as_view(),
        name="estudiante_create",
    ),
    path(
        "estudiantes/<int:pk>/",
        views.EstudianteDetailView.as_view(),
        name="estudiante_detail",
    ),
    path(
        "estudiantes/<int:pk>/editar/",
        views.EstudianteUpdateView.as_view(),
        name="estudiante_update",
    ),
    path(
        "estudiantes/<int:pk>/eliminar/",
        views.EstudianteDeleteView.as_view(),
        name="estudiante_delete",
    ),
]
