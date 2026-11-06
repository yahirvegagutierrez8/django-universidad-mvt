from django.db import models
from django.urls import reverse


class Profesor(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True, verbose_name="correo electrónico")
    especialidad = models.CharField(max_length=150)
    fecha_ingreso = models.DateField(
        null=True, blank=True, verbose_name="fecha de ingreso"
    )

    class Meta:
        verbose_name = "profesor"
        verbose_name_plural = "profesores"
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return self.nombre_completo

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def get_absolute_url(self):
        return reverse("academico:profesor_detail", kwargs={"pk": self.pk})


class Curso(models.Model):
    codigo = models.CharField(max_length=20, unique=True, verbose_name="código")
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, verbose_name="descripción")
    creditos = models.PositiveSmallIntegerField(default=1, verbose_name="créditos")
    # Un profesor imparte varios cursos (1:N). Si se borra el profesor,
    # el curso se conserva sin profesor asignado.
    profesor = models.ForeignKey(
        Profesor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cursos",
    )

    class Meta:
        verbose_name = "curso"
        verbose_name_plural = "cursos"
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    def get_absolute_url(self):
        return reverse("academico:curso_detail", kwargs={"pk": self.pk})


class Estudiante(models.Model):
    matricula = models.CharField(max_length=20, unique=True, verbose_name="matrícula")
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True, verbose_name="correo electrónico")
    fecha_nacimiento = models.DateField(verbose_name="fecha de nacimiento")
    # Un estudiante cursa varios cursos y un curso tiene varios estudiantes (N:M).
    cursos = models.ManyToManyField(Curso, blank=True, related_name="estudiantes")

    class Meta:
        verbose_name = "estudiante"
        verbose_name_plural = "estudiantes"
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.matricula} - {self.nombre_completo}"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def get_absolute_url(self):
        return reverse("academico:estudiante_detail", kwargs={"pk": self.pk})
