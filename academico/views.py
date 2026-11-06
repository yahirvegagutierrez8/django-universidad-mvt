from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import (
    BusquedaCursoForm,
    BusquedaEstudianteForm,
    BusquedaProfesorForm,
    CursoForm,
    EstudianteForm,
    LoginForm,
    ProfesorForm,
    RegistroForm,
)
from .models import Curso, Estudiante, Profesor


# ---------------------------------------------------------------------------
# Autenticación (sesiones)
# ---------------------------------------------------------------------------
class LoginConMensajeView(SuccessMessageMixin, LoginView):
    template_name = "registration/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True
    success_message = "¡Bienvenido(a), %(username)s!"


class RegistroView(SuccessMessageMixin, CreateView):
    form_class = RegistroForm
    template_name = "registration/registro.html"
    success_url = reverse_lazy("login")
    success_message = "Cuenta creada correctamente. Ya puedes iniciar sesión."


# ---------------------------------------------------------------------------
# Mixins reutilizables
# ---------------------------------------------------------------------------
class ListadoBaseView(LoginRequiredMixin, ListView):
    """Listado paginado con búsqueda multi-criterio por GET.

    Las subclases definen `form_class` (un BusquedaBaseForm). Los filtros
    llegan en la URL (?q=...&operador=OR&page=2), se combinan en un objeto Q
    con AND u OR y se aplican ANTES de paginar.
    """

    paginate_by = 5
    form_class = None

    def get_form(self):
        if not hasattr(self, "_form"):
            # Siempre ligado a request.GET: todos los campos son opcionales.
            self._form = self.form_class(self.request.GET)
        return self._form

    def get_queryset(self):
        queryset = super().get_queryset()
        form = self.get_form()
        if form.is_valid():
            queryset = queryset.filter(form.obtener_q())
        # Si el formulario es inválido (p. ej. rango de fechas invertido) se
        # muestra el listado completo junto con los errores del formulario.
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        # Query string SIN "page": los enlaces de paginación lo anteponen
        # y así el estado de la búsqueda se conserva entre páginas.
        contexto["querystring"] = parametros.urlencode()
        contexto["form"] = self.get_form()
        # Hay filtros activos si algún parámetro (salvo page/operador) trae valor.
        contexto["hay_filtros"] = any(
            valor for clave, valor in parametros.items() if clave != "operador"
        )
        return contexto


class FormularioBaseMixin(LoginRequiredMixin, SuccessMessageMixin):
    """Plantilla única para crear/editar con título y botón cancelar."""

    template_name = "academico/formulario.html"
    titulo = ""
    cancelar_url = None

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["titulo"] = self.titulo
        contexto["cancelar_url"] = self.cancelar_url
        return contexto


class EliminarBaseView(LoginRequiredMixin, DeleteView):
    """Confirmación de borrado + mensaje flash de éxito."""

    template_name = "academico/confirmar_eliminar.html"
    tipo = ""
    mensaje_exito = "Registro eliminado correctamente."

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["tipo"] = self.tipo
        contexto["cancelar_url"] = self.object.get_absolute_url()
        return contexto

    def form_valid(self, form):
        descripcion = str(self.object)
        respuesta = super().form_valid(form)
        messages.success(self.request, self.mensaje_exito.format(objeto=descripcion))
        return respuesta


# ---------------------------------------------------------------------------
# Inicio
# ---------------------------------------------------------------------------
class InicioView(LoginRequiredMixin, TemplateView):
    template_name = "academico/inicio.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["total_cursos"] = Curso.objects.count()
        contexto["total_profesores"] = Profesor.objects.count()
        contexto["total_estudiantes"] = Estudiante.objects.count()
        contexto["cursos_sin_profesor"] = Curso.objects.filter(
            profesor__isnull=True
        ).count()
        return contexto


# ---------------------------------------------------------------------------
# Cursos
# ---------------------------------------------------------------------------
class CursoListView(ListadoBaseView):
    model = Curso
    form_class = BusquedaCursoForm

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("profesor")
            .annotate(num_estudiantes=Count("estudiantes", distinct=True))
        )


class CursoDetailView(LoginRequiredMixin, DetailView):
    model = Curso

    def get_queryset(self):
        return Curso.objects.select_related("profesor").prefetch_related("estudiantes")


class CursoCreateView(FormularioBaseMixin, CreateView):
    model = Curso
    form_class = CursoForm
    titulo = "Nuevo curso"
    cancelar_url = reverse_lazy("academico:curso_list")
    success_message = "Curso «%(nombre)s» creado correctamente."


class CursoUpdateView(FormularioBaseMixin, UpdateView):
    model = Curso
    form_class = CursoForm
    titulo = "Editar curso"
    cancelar_url = reverse_lazy("academico:curso_list")
    success_message = "Curso «%(nombre)s» actualizado correctamente."


class CursoDeleteView(EliminarBaseView):
    model = Curso
    tipo = "curso"
    success_url = reverse_lazy("academico:curso_list")
    mensaje_exito = "El curso «{objeto}» fue eliminado."


# ---------------------------------------------------------------------------
# Profesores
# ---------------------------------------------------------------------------
class ProfesorListView(ListadoBaseView):
    model = Profesor
    form_class = BusquedaProfesorForm

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(num_cursos=Count("cursos", distinct=True))
        )


class ProfesorDetailView(LoginRequiredMixin, DetailView):
    model = Profesor

    def get_queryset(self):
        return Profesor.objects.prefetch_related("cursos")


class ProfesorCreateView(FormularioBaseMixin, CreateView):
    model = Profesor
    form_class = ProfesorForm
    titulo = "Nuevo profesor"
    cancelar_url = reverse_lazy("academico:profesor_list")
    success_message = "Profesor(a) %(nombre)s %(apellido)s registrado(a) correctamente."


class ProfesorUpdateView(FormularioBaseMixin, UpdateView):
    model = Profesor
    form_class = ProfesorForm
    titulo = "Editar profesor"
    cancelar_url = reverse_lazy("academico:profesor_list")
    success_message = "Datos de %(nombre)s %(apellido)s actualizados correctamente."


class ProfesorDeleteView(EliminarBaseView):
    model = Profesor
    tipo = "profesor"
    success_url = reverse_lazy("academico:profesor_list")
    mensaje_exito = "El profesor «{objeto}» fue eliminado."


# ---------------------------------------------------------------------------
# Estudiantes
# ---------------------------------------------------------------------------
class EstudianteListView(ListadoBaseView):
    model = Estudiante
    form_class = BusquedaEstudianteForm

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(num_cursos=Count("cursos", distinct=True))
        )


class EstudianteDetailView(LoginRequiredMixin, DetailView):
    model = Estudiante

    def get_queryset(self):
        return Estudiante.objects.prefetch_related("cursos__profesor")


class EstudianteCreateView(FormularioBaseMixin, CreateView):
    model = Estudiante
    form_class = EstudianteForm
    titulo = "Nuevo estudiante"
    cancelar_url = reverse_lazy("academico:estudiante_list")
    success_message = "Estudiante %(nombre)s %(apellido)s registrado(a) correctamente."


class EstudianteUpdateView(FormularioBaseMixin, UpdateView):
    model = Estudiante
    form_class = EstudianteForm
    titulo = "Editar estudiante"
    cancelar_url = reverse_lazy("academico:estudiante_list")
    success_message = "Expediente de %(nombre)s %(apellido)s actualizado correctamente."


class EstudianteDeleteView(EliminarBaseView):
    model = Estudiante
    tipo = "estudiante"
    success_url = reverse_lazy("academico:estudiante_list")
    mensaje_exito = "El expediente «{objeto}» fue eliminado."
