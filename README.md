# Sistema de Gestión Académica Universitaria (Django · MVT)

Proyecto Final Integrador: administración de **Cursos**, **Profesores** y **Estudiantes** con
Vistas Basadas en Clases, ModelForm, autenticación por sesiones, mensajes flash, paginación,
Bootstrap 5 y búsqueda multi-criterio con objetos `Q`.

## Puesta en marcha

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations academico   # genera las migraciones (primer uso)
python manage.py migrate
python manage.py createsuperuser            # opcional: acceso a /admin/
python manage.py cargar_datos               # opcional: datos de ejemplo
python manage.py runserver
```

Abre http://127.0.0.1:8000/ . Sin sesión iniciada te redirige a `/login/`; puedes crear una
cuenta en `/registro/`. Las pruebas se ejecutan con `python manage.py test`.

## Arquitectura (MVT)

| Capa     | Dónde                                           | Contenido                                           |
|----------|-------------------------------------------------|-----------------------------------------------------|
| Model    | `academico/models.py`                           | `Profesor` 1:N `Curso`, `Estudiante` N:M `Curso`    |
| View     | `academico/views.py`                            | CBV: List/Detail/Create/Update/Delete + `LoginRequiredMixin` |
| Template | `templates/`                                    | `base.html` con herencia, parciales, Bootstrap 5    |
| Forms    | `academico/forms.py`                            | `ModelForm` de edición y formularios de búsqueda    |

## Búsqueda multi-criterio (GET + Q + paginación)

* Cada listado tiene un panel «Búsqueda avanzada» con un formulario `method="get"`.
  Los criterios viajan en la URL, p. ej.
  `/cursos/?q=PRO&creditos_min=5&operador=OR&page=2`.
* `BusquedaBaseForm.criterios()` devuelve una lista de objetos `Q` (uno por filtro llenado) y
  `obtener_q()` los combina con `&` (AND) o `|` (OR) según el campo **operador**.
  El texto libre `q` busca internamente con OR en varios campos.
* La vista aplica `queryset.filter(form.obtener_q())` **antes** de paginar.
* `get_context_data` entrega `querystring` (los parámetros GET sin `page`) y el parcial
  `_paginacion.html` lo agrega a cada enlace (`?page=2&q=...`), de modo que los filtros
  se conservan al cambiar de página.

| Listado      | Criterios                                                                  |
|--------------|----------------------------------------------------------------------------|
| Cursos       | texto libre, profesor, créditos mín./máx., solo sin profesor               |
| Profesores   | texto libre, especialidad, fecha de ingreso desde/hasta                    |
| Estudiantes  | texto libre, inscrito en curso, fecha de nacimiento desde/hasta            |
