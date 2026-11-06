import datetime

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from .forms import CursoForm
from .models import Curso, Estudiante, Profesor


def crear_profesor(n=1):
    return Profesor.objects.create(
        nombre=f"Nombre{n}",
        apellido=f"Apellido{n}",
        email=f"profe{n}@uni.mx",
        especialidad="Informática",
    )


class AccesoTests(TestCase):
    def test_vistas_protegidas_redirigen_al_login(self):
        nombres = [
            "academico:inicio",
            "academico:curso_list",
            "academico:profesor_list",
            "academico:estudiante_list",
            "academico:curso_create",
            "academico:profesor_create",
            "academico:estudiante_create",
        ]
        for nombre in nombres:
            with self.subTest(vista=nombre):
                respuesta = self.client.get(reverse(nombre))
                self.assertEqual(respuesta.status_code, 302)
                self.assertIn(reverse("login"), respuesta.url)

    def test_login_correcto_inicia_sesion(self):
        User.objects.create_user("ana", password="ClaveSegura123")
        respuesta = self.client.post(
            reverse("login"), {"username": "ana", "password": "ClaveSegura123"}
        )
        self.assertRedirects(respuesta, reverse("academico:inicio"))

    def test_registro_crea_usuario(self):
        respuesta = self.client.post(
            reverse("registro"),
            {
                "username": "nuevo",
                "password1": "ClaveMuySegura987",
                "password2": "ClaveMuySegura987",
            },
        )
        self.assertRedirects(respuesta, reverse("login"))
        self.assertTrue(User.objects.filter(username="nuevo").exists())


class CrudTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("tester", password="ClaveSegura123")
        self.client.login(username="tester", password="ClaveSegura123")

    def test_crear_curso_con_mensaje_flash(self):
        profesor = crear_profesor()
        respuesta = self.client.post(
            reverse("academico:curso_create"),
            {
                "codigo": "mat101",
                "nombre": "Cálculo",
                "descripcion": "Intro",
                "creditos": 8,
                "profesor": profesor.pk,
            },
        )
        self.assertRedirects(
            respuesta, Curso.objects.get().get_absolute_url(), fetch_redirect_response=False
        )
        curso = Curso.objects.get()
        self.assertEqual(curso.codigo, "MAT101")  # normalizado a mayúsculas
        mensajes = [str(m) for m in get_messages(respuesta.wsgi_request)]
        self.assertTrue(any("creado" in m for m in mensajes))

    def test_codigo_de_curso_duplicado_es_invalido(self):
        Curso.objects.create(codigo="PRO101", nombre="Programación", creditos=6)
        form = CursoForm(
            data={"codigo": "pro101", "nombre": "Otro", "creditos": 6, "descripcion": ""}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("codigo", form.errors)

    def test_creditos_fuera_de_rango_es_invalido(self):
        form = CursoForm(
            data={"codigo": "X1", "nombre": "Otro", "creditos": 99, "descripcion": ""}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("creditos", form.errors)

    def test_editar_profesor(self):
        profesor = crear_profesor()
        respuesta = self.client.post(
            reverse("academico:profesor_update", args=[profesor.pk]),
            {
                "nombre": "Nuevo",
                "apellido": profesor.apellido,
                "email": profesor.email,
                "especialidad": "IA",
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        profesor.refresh_from_db()
        self.assertEqual(profesor.nombre, "Nuevo")

    def test_crear_estudiante_con_cursos(self):
        c1 = Curso.objects.create(codigo="A1", nombre="Uno", creditos=4)
        c2 = Curso.objects.create(codigo="A2", nombre="Dos", creditos=4)
        respuesta = self.client.post(
            reverse("academico:estudiante_create"),
            {
                "matricula": "20260001",
                "nombre": "Luis",
                "apellido": "Pérez",
                "email": "luis@uni.mx",
                "fecha_nacimiento": "2004-05-20",
                "cursos": [c1.pk, c2.pk],
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        estudiante = Estudiante.objects.get()
        self.assertEqual(estudiante.cursos.count(), 2)

    def test_eliminar_estudiante_muestra_mensaje(self):
        estudiante = Estudiante.objects.create(
            matricula="1",
            nombre="A",
            apellido="B",
            email="a@uni.mx",
            fecha_nacimiento=datetime.date(2003, 1, 1),
        )
        respuesta = self.client.post(
            reverse("academico:estudiante_delete", args=[estudiante.pk])
        )
        self.assertRedirects(respuesta, reverse("academico:estudiante_list"))
        self.assertFalse(Estudiante.objects.exists())
        mensajes = [str(m) for m in get_messages(respuesta.wsgi_request)]
        self.assertTrue(any("eliminado" in m for m in mensajes))

    def test_borrar_profesor_conserva_el_curso(self):
        profesor = crear_profesor()
        curso = Curso.objects.create(
            codigo="Z9", nombre="Curso", creditos=3, profesor=profesor
        )
        profesor.delete()
        curso.refresh_from_db()
        self.assertIsNone(curso.profesor)


class PaginacionYBusquedaTests(TestCase):
    def setUp(self):
        User.objects.create_user("tester", password="ClaveSegura123")
        self.client.login(username="tester", password="ClaveSegura123")
        for n in range(1, 8):  # 7 profesores -> 2 páginas de 5
            crear_profesor(n)

    def test_primera_pagina_tiene_cinco_registros(self):
        respuesta = self.client.get(reverse("academico:profesor_list"))
        self.assertEqual(len(respuesta.context["page_obj"]), 5)
        self.assertTrue(respuesta.context["is_paginated"])

    def test_segunda_pagina_tiene_los_restantes(self):
        respuesta = self.client.get(reverse("academico:profesor_list"), {"page": 2})
        self.assertEqual(len(respuesta.context["page_obj"]), 2)

    def test_busqueda_por_texto_libre(self):
        respuesta = self.client.get(reverse("academico:profesor_list"), {"q": "Nombre3"})
        self.assertEqual(len(respuesta.context["page_obj"]), 1)
        self.assertTrue(respuesta.context["hay_filtros"])

    def test_paginacion_conserva_los_filtros(self):
        # 7 resultados que coinciden con "profe" (en el correo) -> 2 páginas.
        respuesta = self.client.get(
            reverse("academico:profesor_list"), {"q": "profe", "operador": "OR"}
        )
        self.assertIn("q=profe", respuesta.context["querystring"])
        self.assertIn("operador=OR", respuesta.context["querystring"])
        self.assertContains(respuesta, "?page=2&amp;q=profe")
        self.assertNotIn("page=", respuesta.context["querystring"])


class BusquedaMultiCriterioTests(TestCase):
    def setUp(self):
        User.objects.create_user("tester", password="ClaveSegura123")
        self.client.login(username="tester", password="ClaveSegura123")
        self.p1 = Profesor.objects.create(
            nombre="Laura", apellido="Martínez", email="l@uni.mx", especialidad="Matemáticas"
        )
        self.p2 = Profesor.objects.create(
            nombre="Carlos", apellido="Hernández", email="c@uni.mx", especialidad="Programación"
        )
        self.c1 = Curso.objects.create(codigo="MAT101", nombre="Cálculo", creditos=8, profesor=self.p1)
        self.c2 = Curso.objects.create(codigo="PRO101", nombre="Python", creditos=6, profesor=self.p2)
        self.c3 = Curso.objects.create(codigo="PRO201", nombre="Django", creditos=4)  # sin profesor

    def codigos(self, params):
        respuesta = self.client.get(reverse("academico:curso_list"), params)
        return {c.codigo for c in respuesta.context["page_obj"]}

    def test_sin_filtros_devuelve_todo(self):
        self.assertEqual(self.codigos({}), {"MAT101", "PRO101", "PRO201"})

    def test_and_exige_todos_los_criterios(self):
        resultado = self.codigos({"q": "PRO", "creditos_min": 5, "operador": "AND"})
        self.assertEqual(resultado, {"PRO101"})

    def test_or_acepta_cualquier_criterio(self):
        resultado = self.codigos({"q": "MAT", "creditos_max": 4, "operador": "OR"})
        self.assertEqual(resultado, {"MAT101", "PRO201"})

    def test_operador_por_defecto_es_and(self):
        self.assertEqual(self.codigos({"q": "PRO", "creditos_min": 5}), {"PRO101"})

    def test_filtro_por_profesor(self):
        self.assertEqual(self.codigos({"profesor": self.p1.pk}), {"MAT101"})

    def test_filtro_sin_profesor(self):
        self.assertEqual(self.codigos({"sin_profesor": "on"}), {"PRO201"})

    def test_texto_libre_busca_en_nombre_del_profesor(self):
        self.assertEqual(self.codigos({"q": "Hernández"}), {"PRO101"})

    def test_rango_invertido_muestra_error_y_no_filtra(self):
        respuesta = self.client.get(
            reverse("academico:curso_list"), {"creditos_min": 9, "creditos_max": 2}
        )
        self.assertIn("creditos_max", respuesta.context["form"].errors)
        self.assertEqual(len(respuesta.context["page_obj"]), 3)

    def test_filtro_estudiantes_por_curso_conserva_conteo(self):
        e = Estudiante.objects.create(
            matricula="1", nombre="A", apellido="B", email="a@uni.mx",
            fecha_nacimiento=datetime.date(2003, 1, 1),
        )
        e.cursos.set([self.c1, self.c2])
        respuesta = self.client.get(
            reverse("academico:estudiante_list"), {"curso": self.c1.pk}
        )
        resultados = list(respuesta.context["page_obj"])
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0].num_cursos, 2)  # no se reduce por el filtro

    def test_filtro_profesores_por_fecha_de_ingreso(self):
        self.p1.fecha_ingreso = datetime.date(2015, 1, 1)
        self.p1.save()
        self.p2.fecha_ingreso = datetime.date(2022, 1, 1)
        self.p2.save()
        respuesta = self.client.get(
            reverse("academico:profesor_list"), {"ingreso_desde": "2020-01-01"}
        )
        self.assertEqual([p.pk for p in respuesta.context["page_obj"]], [self.p2.pk])
