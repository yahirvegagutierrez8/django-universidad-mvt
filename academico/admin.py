from django.contrib import admin

from .models import Curso, Estudiante, Profesor


@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ("apellido", "nombre", "email", "especialidad")
    search_fields = ("nombre", "apellido", "email", "especialidad")


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "creditos", "profesor")
    list_filter = ("profesor",)
    search_fields = ("codigo", "nombre")


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ("matricula", "apellido", "nombre", "email")
    search_fields = ("matricula", "nombre", "apellido", "email")
    filter_horizontal = ("cursos",)
