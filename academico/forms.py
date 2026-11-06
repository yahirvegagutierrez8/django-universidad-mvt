from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q

from .models import Curso, Estudiante, Profesor


class BootstrapFormMixin:
    """Aplica clases de Bootstrap 5 a todos los widgets del formulario."""

    def _aplicar_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxSelectMultiple):
                clase = "form-check-input"
            elif isinstance(widget, forms.CheckboxInput):
                clase = "form-check-input"
            elif isinstance(widget, forms.Select):
                clase = "form-select"
            else:
                clase = "form-control"
            existente = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existente} {clase}".strip()


class ProfesorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Profesor
        fields = ["nombre", "apellido", "email", "especialidad", "fecha_ingreso"]
        widgets = {
            "fecha_ingreso": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_bootstrap()


class CursoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Curso
        fields = ["codigo", "nombre", "descripcion", "creditos", "profesor"]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["profesor"].empty_label = "— Sin profesor asignado —"
        self._aplicar_bootstrap()

    def clean_creditos(self):
        creditos = self.cleaned_data["creditos"]
        if creditos < 1 or creditos > 20:
            raise forms.ValidationError("Los créditos deben estar entre 1 y 20.")
        return creditos

    def clean_codigo(self):
        # Normaliza el código a mayúsculas para evitar duplicados "mat101"/"MAT101".
        codigo = self.cleaned_data["codigo"].strip().upper()
        existe = Curso.objects.filter(codigo=codigo)
        if self.instance.pk:
            existe = existe.exclude(pk=self.instance.pk)
        if existe.exists():
            raise forms.ValidationError("Ya existe un curso con este código.")
        return codigo


class EstudianteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Estudiante
        fields = [
            "matricula",
            "nombre",
            "apellido",
            "email",
            "fecha_nacimiento",
            "cursos",
        ]
        widgets = {
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "cursos": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_bootstrap()


# ---------------------------------------------------------------------------
# Formularios de BÚSQUEDA (se envían por GET, no modifican datos)
# ---------------------------------------------------------------------------
OPERADORES = [
    ("AND", "Cumplir TODOS los criterios (AND)"),
    ("OR", "Cumplir ALGUNO de los criterios (OR)"),
]


class BusquedaBaseForm(BootstrapFormMixin, forms.Form):
    """Base de los buscadores multi-criterio.

    Cada subclase implementa `criterios()`, que devuelve una lista de objetos Q
    (uno por cada filtro que el usuario llenó). `obtener_q()` los combina con
    el operador lógico elegido: AND (&) u OR (|).
    """

    operador = forms.ChoiceField(
        choices=OPERADORES,
        required=False,
        initial="AND",
        label="Combinar criterios",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_bootstrap()

    def clean_operador(self):
        return self.cleaned_data.get("operador") or "AND"

    def criterios(self):
        raise NotImplementedError

    def obtener_q(self):
        criterios = self.criterios()
        if not criterios:
            return Q()  # sin filtros: Q() vacío no restringe nada
        combinado = criterios[0]
        for criterio in criterios[1:]:
            if self.cleaned_data["operador"] == "OR":
                combinado = combinado | criterio
            else:
                combinado = combinado & criterio
        return combinado

    def _validar_rango(self, minimo, maximo, mensaje):
        a, b = self.cleaned_data.get(minimo), self.cleaned_data.get(maximo)
        if a is not None and b is not None and a > b:
            self.add_error(maximo, mensaje)


class BusquedaCursoForm(BusquedaBaseForm):
    q = forms.CharField(
        required=False,
        label="Texto libre",
        widget=forms.TextInput(attrs={"placeholder": "Código, nombre, descripción o profesor"}),
    )
    profesor = forms.ModelChoiceField(
        queryset=Profesor.objects.all(),
        required=False,
        label="Profesor",
        empty_label="— Cualquiera —",
    )
    creditos_min = forms.IntegerField(required=False, min_value=0, label="Créditos desde")
    creditos_max = forms.IntegerField(required=False, min_value=0, label="Créditos hasta")
    sin_profesor = forms.BooleanField(required=False, label="Solo cursos sin profesor")

    def clean(self):
        datos = super().clean()
        self._validar_rango(
            "creditos_min", "creditos_max", "Debe ser mayor o igual que «Créditos desde»."
        )
        return datos

    def criterios(self):
        d = self.cleaned_data
        criterios = []
        if d.get("q"):
            t = d["q"].strip()
            criterios.append(
                Q(codigo__icontains=t)
                | Q(nombre__icontains=t)
                | Q(descripcion__icontains=t)
                | Q(profesor__nombre__icontains=t)
                | Q(profesor__apellido__icontains=t)
            )
        if d.get("profesor"):
            criterios.append(Q(profesor=d["profesor"]))
        if d.get("creditos_min") is not None:
            criterios.append(Q(creditos__gte=d["creditos_min"]))
        if d.get("creditos_max") is not None:
            criterios.append(Q(creditos__lte=d["creditos_max"]))
        if d.get("sin_profesor"):
            criterios.append(Q(profesor__isnull=True))
        return criterios


class BusquedaProfesorForm(BusquedaBaseForm):
    q = forms.CharField(
        required=False,
        label="Texto libre",
        widget=forms.TextInput(attrs={"placeholder": "Nombre, apellido o correo"}),
    )
    especialidad = forms.CharField(required=False, label="Especialidad")
    ingreso_desde = forms.DateField(
        required=False, label="Ingreso desde", widget=forms.DateInput(attrs={"type": "date"})
    )
    ingreso_hasta = forms.DateField(
        required=False, label="Ingreso hasta", widget=forms.DateInput(attrs={"type": "date"})
    )

    def clean(self):
        datos = super().clean()
        self._validar_rango(
            "ingreso_desde", "ingreso_hasta", "Debe ser posterior a «Ingreso desde»."
        )
        return datos

    def criterios(self):
        d = self.cleaned_data
        criterios = []
        if d.get("q"):
            t = d["q"].strip()
            criterios.append(
                Q(nombre__icontains=t) | Q(apellido__icontains=t) | Q(email__icontains=t)
            )
        if d.get("especialidad"):
            criterios.append(Q(especialidad__icontains=d["especialidad"].strip()))
        if d.get("ingreso_desde"):
            criterios.append(Q(fecha_ingreso__gte=d["ingreso_desde"]))
        if d.get("ingreso_hasta"):
            criterios.append(Q(fecha_ingreso__lte=d["ingreso_hasta"]))
        return criterios


class BusquedaEstudianteForm(BusquedaBaseForm):
    q = forms.CharField(
        required=False,
        label="Texto libre",
        widget=forms.TextInput(attrs={"placeholder": "Matrícula, nombre, apellido o correo"}),
    )
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.all(),
        required=False,
        label="Inscrito en el curso",
        empty_label="— Cualquiera —",
    )
    nacido_desde = forms.DateField(
        required=False, label="Nacido desde", widget=forms.DateInput(attrs={"type": "date"})
    )
    nacido_hasta = forms.DateField(
        required=False, label="Nacido hasta", widget=forms.DateInput(attrs={"type": "date"})
    )

    def clean(self):
        datos = super().clean()
        self._validar_rango(
            "nacido_desde", "nacido_hasta", "Debe ser posterior a «Nacido desde»."
        )
        return datos

    def criterios(self):
        d = self.cleaned_data
        criterios = []
        if d.get("q"):
            t = d["q"].strip()
            criterios.append(
                Q(matricula__icontains=t)
                | Q(nombre__icontains=t)
                | Q(apellido__icontains=t)
                | Q(email__icontains=t)
            )
        if d.get("curso"):
            # Subconsulta por pk: evita un JOIN que alteraría el Count("cursos")
            # que el listado anota después.
            criterios.append(
                Q(pk__in=Estudiante.objects.filter(cursos=d["curso"]).values("pk"))
            )
        if d.get("nacido_desde"):
            criterios.append(Q(fecha_nacimiento__gte=d["nacido_desde"]))
        if d.get("nacido_hasta"):
            criterios.append(Q(fecha_nacimiento__lte=d["nacido_hasta"]))
        return criterios


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_bootstrap()


class RegistroForm(BootstrapFormMixin, UserCreationForm):
    """Alta de usuarios del sistema (personal administrativo)."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_bootstrap()
