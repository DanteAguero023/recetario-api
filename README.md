# Mi Recetario — de la web a la API REST

Unidad 3 · Programación Back End (INACAP). Una app Django de recetas con **dos puertas a la misma base de datos**:

- **Web** (HTML): sesión + CSRF.
- **API REST** (`/api/`): token JWT, con las mismas reglas de validación y de autoría.

Modelo `Receta`: `titulo`, `ingredientes`, `preparacion`, `tiempo_minutos`, `dificultad` (campos propios), más `autor` (FK a `User`) y `creado`.

## Cómo correrlo

```bash
git clone <URL-del-repo> && cd mi_recetario
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # y cambia SECRET_KEY (y ADMIN_URL si quieres) por valores propios
python manage.py migrate
python manage.py cargar_demo    # opcional: usuarios ana y beto con recetas de ejemplo
python manage.py runserver
```

- Web: <http://127.0.0.1:8000/> · API navegable: `/api/`
- Admin: `/gestion-recetas/` (la ruta sale de `ADMIN_URL` en `.env`; crea el usuario con `python manage.py createsuperuser`)
  - **Ojo:** `/admin/` devuelve 404 a propósito (auditoría OWASP API5). Si quieres volver a esa ruta, cambia o borra `ADMIN_URL` en `.env` y reinicia el servidor.
- Usuarios demo (solo desarrollo): `ana` / `Ana-Recetas-2026` y `beto` / `Beto-Recetas-2026`
- El archivo `.env` **no se sube** (está en `.gitignore`); `.env.example` muestra qué variables hacen falta.
- Pruebas: `python manage.py test recetas` (29 tests).

## Parte 1 · App web

| Requisito | Dónde |
|---|---|
| CRUD con vistas genéricas | `recetas/views.py` (`ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`) |
| Validación propia en el servidor | `recetas/validators.py` (mínimo 2 ingredientes, uno por línea), tiempo entre 1 y 1440 min en el modelo, título de 3+ caracteres en `forms.py` |
| Registro, login, logout | `RegistroView` (entra directo tras registrarse) y `django.contrib.auth.urls` bajo `/cuentas/` (logout por POST con CSRF) |
| Solo el autor edita o borra | `SoloAutorMixin`: otro usuario recibe **403** |

El autor nunca viene del formulario: `form_valid` asigna `request.user`.

### Páginas web y diseño

| URL | Página | Acceso |
|---|---|---|
| `/` | Recetas de la comunidad (tarjetas, paginadas) | pública |
| `/receta/<id>/` | Detalle | pública |
| `/dashboard/` | Resumen personal: mis recetas, tiempo promedio, reparto por dificultad y últimas recetas | login |
| `/configuracion/` | Tema claro/oscuro/automático, tamaño de texto, animaciones, splash y cambio de contraseña | login |

- **Estilos**: `recetas/static/recetas/styles.css` (paleta burdeos y rojos con variables CSS, modo oscuro) y `app.js` (splash y preferencias).
- **Splash de bienvenida**: aparece una vez por sesión del navegador y de nuevo al ingresar; se cierra solo o con un toque.
- **Responsive**: en teléfono hay barra inferior de navegación; desde 768 px pasa a menú superior. Las grillas se adaptan a 1, 2 o 3 columnas.
- **Animaciones**: entrada escalonada de tarjetas, barras del dashboard y transiciones. Se pueden apagar en Configuración y respetan `prefers-reduced-motion`.
- Las preferencias se guardan en `localStorage` del navegador, no en la base de datos.
- Con `DEBUG=False`, Django no sirve los archivos estáticos: hay que ejecutar `collectstatic` y servirlos con el servidor web o WhiteNoise.

## Parte 2 · API REST

### Endpoints

| Método | URL | Qué hace | Auth |
|---|---|---|---|
| POST | `/api/token/` | Entrega `access` (30 min) y `refresh` (1 día) | — |
| POST | `/api/token/refresh/` | Nuevo `access` (y un `refresh` nuevo; el anterior se revoca) | refresh |
| GET | `/api/recetas/` | Lista paginada (10 por página) | pública |
| POST | `/api/recetas/` | Crea (el autor es el dueño del token) → 201 | JWT |
| GET | `/api/recetas/{id}/` | Detalle | pública |
| PUT / PATCH | `/api/recetas/{id}/` | Reemplaza / modifica | JWT + ser el autor |
| DELETE | `/api/recetas/{id}/` | Borra → 204 | JWT + ser el autor |
| GET | `/api/recetas/mios/` | Solo las recetas del usuario del token | JWT |

### Cómo cumple cada AE

- **3.1.1 Configuración**: `rest_framework`, `rest_framework_simplejwt.token_blacklist` y `corsheaders` en `INSTALLED_APPS`; `REST_FRAMEWORK` y `SIMPLE_JWT` en `settings.py` según la documentación oficial; las dependencias están fijadas en `requirements.txt`.
- **3.1.3 JSON**: `RecetaSerializer` (`recetas/serializers.py`) con `fields` explícitos (nunca `__all__`) y `autor` de solo lectura (`ReadOnlyField(source="autor.username")`). Las validaciones viven en el modelo, así la web y la API aplican exactamente las mismas.
- **3.1.4 API RESTful**: `RecetaViewSet` (`ModelViewSet`) + `DefaultRouter`, más la acción `mios` (`@action(detail=False)`).
- **3.1.2 Autenticación**: SimpleJWT + permiso `EsAutorOSoloLectura` (`recetas/permissions.py`) sobre `IsAuthenticatedOrReadOnly`.

### Demostración de códigos HTTP

Salida real del servidor local (tokens recortados):

```bash
# 200 · listar sin token
$ curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:8000/api/recetas/
HTTP 200

# 401 · crear sin token
$ curl -s -w "\nHTTP %{http_code}\n" -X POST http://127.0.0.1:8000/api/recetas/ \
    -H 'Content-Type: application/json' -d '{"titulo":"Sopa"}'
{"detail":"Las credenciales de autenticación no se proveyeron."}
HTTP 401

# Obtener el token
$ curl -s -X POST http://127.0.0.1:8000/api/token/ \
    -H 'Content-Type: application/json' -d '{"username":"ana","password":"Ana-Recetas-2026"}'
{"refresh":"eyJhbGciOiJIUzI1NiIsInR5c...","access":"eyJhbGciOiJIUzI1NiIsInR5c..."}

# 201 · crear con token (el autor sale del token, no del cuerpo)
$ curl -s -w "\nHTTP %{http_code}\n" -X POST http://127.0.0.1:8000/api/recetas/ \
    -H "Authorization: Bearer $ACCESS_ANA" -H 'Content-Type: application/json' \
    -d '{"titulo":"Sopa de zapallo","ingredientes":"1 zapallo\n1 cebolla","preparacion":"Hervir y moler.","tiempo_minutos":40,"dificultad":"media"}'
{"id":4,"titulo":"Sopa de zapallo",...,"autor":"ana","creado":"2026-09-30T20:42:08-03:00"}
HTTP 201

# 403 · beto intenta borrar una receta de ana
$ curl -s -w "\nHTTP %{http_code}\n" -X DELETE http://127.0.0.1:8000/api/recetas/1/ \
    -H "Authorization: Bearer $ACCESS_BETO"
{"detail":"Solo el autor puede modificar esta receta."}
HTTP 403
```

### Pruebas automáticas

`python manage.py test recetas` → **29 tests OK**.

| Archivo | Qué comprueba |
|---|---|
| `recetas/tests.py` (15) | Web: lista/detalle públicos, crear exige login, autor asignado por el servidor, validaciones, autor edita/borra, ajeno recibe 403, registro + login + logout, dashboard (solo cuenta lo propio), configuración y cambio de contraseña, login redirige al dashboard |
| `recetas/tests_api.py` (14) | API: 200 al listar (paginado), 401 sin token, JWT + 201, el `autor` enviado por el cliente se ignora, campos expuestos exactos, 400 por validación, 403 en PUT/PATCH/DELETE ajeno, `/mios/`, refresh rotado y revocado, throttling (429) en la API y en `/api/token/`, bloqueo de la cuenta tras 5 logins fallidos |

## Auditoría de seguridad con IA (OWASP API Security Top 10, 2023)

**Cómo se trabajó.** La IA (Claude Code, modelo Sonnet 5.5) actuó como **copiloto**: leyó los archivos reales (`settings.py`, `serializers.py`, `permissions.py`, `api_views.py`), explicó cada riesgo OWASP y **propuso** cambios. **Las decisiones las tomó el autor**: para las recomendaciones que tenían costos o alternativas, eligió cuáles aplicar y cuáles rechazar. Lo aplicado se verificó con pruebas o con `manage.py check --deploy`.

**Prompt usado:**

> Actúa como mi copiloto de seguridad. Revisa `settings.py`, `serializers.py`, `permissions.py` y `api_views.py` de esta API de recetas (Django REST Framework + SimpleJWT) contra el OWASP API Security Top 10 (2023). Para cada riesgo dime si aplica, qué falta y qué cambio concreto propones, con sus costos. Basa las propuestas en la documentación oficial; no inventes configuraciones. Yo decido qué se aplica y qué se rechaza.

| # OWASP | Recomendación de la IA | Decisión del autor | Por qué |
|---|---|---|---|
| API1 · Autorización a nivel de objeto | Comprobar la autoría en cada objeto, no solo el login | **Aplicada** | `EsAutorOSoloLectura.has_object_permission`; tests de 403 en PUT/PATCH/DELETE ajeno |
| API2 · Autenticación rota | Access token corto; refresh con rotación y lista negra | **Aplicada** | `ACCESS_TOKEN_LIFETIME` 30 min, `ROTATE_REFRESH_TOKENS` y `BLACKLIST_AFTER_ROTATION`; test de refresh revocado |
| API2 · Fuerza bruta en el login | Limitar intentos en `/api/token/` | **Aplicada** | El throttling global también cubre ese endpoint; test: el intento 31 del minuto recibe 429 |
| API2 · Bloqueo tras logins fallidos | Bloquear la cuenta tras N intentos (`django-axes`) | **Aplicada** | 5 fallos bloquean 15 min (`AXES_FAILURE_LIMIT`, `AXES_COOLOFF_TIME`); test: con la cuenta bloqueada ni la clave correcta entrega token. Al integrarlo hubo que indicar el `backend` en el login automático del registro |
| API2 · Segundo factor (2FA) | Añadir 2FA | **Rechazada** | Excede el alcance del ejercicio y exige paquetes y flujos extra; el throttling y el bloqueo mitigan el riesgo principal |
| API3 · Exposición de propiedades | `fields` explícitos y `autor` de solo lectura | **Aplicada** | Nunca `__all__`; `perform_create` asigna `request.user`; test: un `autor` enviado por el cliente se ignora |
| API4 · Consumo de recursos | Throttling | **Aplicada** | `anon` 30/min y `user` 120/min; test de 429 |
| API4 · Consumo de recursos | Paginar las listas | **Aplicada** | `PageNumberPagination`, `PAGE_SIZE = 10` |
| API4 · Consumo de recursos | Tope de tamaño en `ingredientes` y `preparacion` (eran `TextField` sin límite) | **Aplicada** | `MaxLengthValidator` de 2000 y 10000 caracteres en el modelo (migración `0002`); test de 400 |
| API5 · Autorización a nivel de función | Separar lectura de escritura | **Aplicada** | `IsAuthenticatedOrReadOnly` por defecto; `/mios/` exige `IsAuthenticated`; nunca `AllowAny` |
| API5 · Panel admin | Mover `/admin/` a otra URL | **Aplicada** | La ruta sale de `ADMIN_URL` en `.env` (hoy `gestion-recetas/`). Reduce el ruido de escaneos automáticos; no reemplaza el login de staff |
| API6 · Flujos de negocio sensibles | Captcha o límite al registro | **Rechazada** | El registro es solo web y la API no crea usuarios; no hay un flujo de valor que abusar |
| API7 · SSRF | Validar URLs que el servidor consuma | **No aplica** | El servidor no hace peticiones a URLs del usuario |
| API8 · Mala configuración | Secretos fuera del código | **Aplicada** | `SECRET_KEY` y `DEBUG` vienen de `.env` (python-decouple, `DEBUG` por defecto `False`); `.env` en `.gitignore` |
| API8 · Mala configuración | CORS restringido | **Aplicada** | `CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]`, sin `CORS_ALLOW_ALL_ORIGINS`; `ALLOWED_HOSTS` también sale de `.env` |
| API8 · Mala configuración | HTTPS, HSTS y cookies seguras | **Aplicada** | Con `DEBUG=False` se activan `SECURE_SSL_REDIRECT`, cookies `Secure` y HSTS (3600 s al inicio). En desarrollo no cambian nada. `check --deploy` con `DEBUG=False` solo deja el aviso opcional de HSTS preload |
| API9 · Inventario inadecuado | Versionar la API (`/api/v1/`) | **Rechazada** | Hay una sola versión y un solo consumidor; versionar cambiaría todas las URLs sin beneficio hoy |
| API9 · Inventario inadecuado | Dejar solo JSON (sin la API navegable) | **Rechazada** | La vista navegable sirve para probar y explicar la API durante el curso |
| API10 · Consumo inseguro de APIs | Validar datos de APIs externas | **No aplica** | No se consume ninguna API externa |

## Estructura

```
mi_recetario/          configuración (settings.py, urls.py)
recetas/
  models.py  validators.py  forms.py  views.py  urls.py        ← web
  serializers.py  permissions.py  api_views.py  api_urls.py    ← API
  templates/  tests.py  tests_api.py  management/commands/cargar_demo.py
```
