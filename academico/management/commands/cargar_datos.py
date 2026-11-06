"""Carga datos de ejemplo para probar listados, relaciones y paginación.

Uso:  python manage.py cargar_datos
"""
import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from academico.models import Curso, Estudiante, Profesor

PROFESORES = [
    ("Laura", "Martínez", "laura.martinez@uni.mx", "Matemáticas"),
    ("Carlos", "Hernández", "carlos.hernandez@uni.mx", "Programación"),
    ("Ana", "López", "ana.lopez@uni.mx", "Bases de datos"),
    ("Jorge", "Ramírez", "jorge.ramirez@uni.mx", "Redes"),
    ("Sofía", "Torres", "sofia.torres@uni.mx", "Ingeniería de software"),
    ("Miguel", "Flores", "miguel.flores@uni.mx", "Física"),
    ("Elena", "Castillo", "elena.castillo@uni.mx", "Estadística"),
]

CURSOS = [
    ("MAT101", "Cálculo Diferencial", 8, 0),
    ("PRO101", "Fundamentos de Programación", 8, 1),
    ("PRO201", "Programación Web con Django", 6, 1),
    ("BDD201", "Bases de Datos Relacionales", 6, 2),
    ("RED301", "Redes de Computadoras", 6, 3),
    ("ING301", "Ingeniería de Software", 7, 4),
    ("FIS101", "Física General", 8, 5),
    ("EST201", "Probabilidad y Estadística", 6, 6),
]

NOMBRES = ["Valeria", "Diego", "Camila", "Mateo", "Renata", "Santiago", "Ximena", "Emilio"]
APELLIDOS = ["García", "Rodríguez", "Pérez", "Sánchez", "Gómez", "Díaz", "Vargas", "Mendoza"]


class Command(BaseCommand):
    help = "Carga profesores, cursos y estudiantes de ejemplo (idempotente)."

    @transaction.atomic
    def handle(self, *args, **options):
        profesores = []
        for nombre, apellido, email, especialidad in PROFESORES:
            profesor, _ = Profesor.objects.get_or_create(
                email=email,
                defaults={
                    "nombre": nombre,
                    "apellido": apellido,
                    "especialidad": especialidad,
                    "fecha_ingreso": datetime.date(2018, 8, 15),
                },
            )
            profesores.append(profesor)

        cursos = []
        for codigo, nombre, creditos, idx_prof in CURSOS:
            curso, _ = Curso.objects.get_or_create(
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "creditos": creditos,
                    "descripcion": f"Curso de {nombre.lower()}.",
                    "profesor": profesores[idx_prof],
                },
            )
            cursos.append(curso)

        for i in range(12):
            matricula = f"2026{i + 1:04d}"
            estudiante, creado = Estudiante.objects.get_or_create(
                matricula=matricula,
                defaults={
                    "nombre": NOMBRES[i % len(NOMBRES)],
                    "apellido": APELLIDOS[(i * 3) % len(APELLIDOS)],
                    "email": f"alumno{i + 1}@uni.mx",
                    "fecha_nacimiento": datetime.date(2004 + i % 3, (i % 12) + 1, 10),
                },
            )
            if creado:
                estudiante.cursos.set([cursos[i % len(cursos)], cursos[(i + 2) % len(cursos)]])

        self.stdout.write(
            self.style.SUCCESS(
                f"Datos listos: {Profesor.objects.count()} profesores, "
                f"{Curso.objects.count()} cursos, {Estudiante.objects.count()} estudiantes."
            )
        )
