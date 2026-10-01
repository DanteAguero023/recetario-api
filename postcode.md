# Pruebas de la API con Postcode / Postman / Thunder Client

Datos para probar los endpoints de `mi_recetario` desde un cliente de API. Sirve igual en Postman, Thunder Client o Insomnia.

## 1. Preparación

1. Levantar el servidor: `python manage.py runserver`
2. Crear los usuarios de prueba (una vez): `python manage.py cargar_demo`

| Usuario | Clave | Rol |
|---|---|---|
| `ana` | `Ana-Recetas-2026` | usuario normal |
| `beto` | `Beto-Recetas-2026` | usuario normal (el "ajeno" en las pruebas de 403) |

3. Variables de entorno en el cliente:

| Variable | Valor |
|---|---|
| `API` | `http://127.0.0.1:8000/api` |
| `TOKEN` | el `access` del login (dura 30 min) |
| `REFRESH` | el `refresh` del login (dura 1 día) |
| `ID` | el `id` de una receta, para detalle, edición y borrado |

Recomendación: dos entornos, uno con el token de `ana` y otro con el de `beto`, para cambiar de usuario con un clic.

> ⚠️ **Antes de probar logins incorrectos:** el proyecto usa `django-axes`. **5 logins fallidos desde tu IP bloquean todos los logins desde esa IP durante 15 minutos** (también en la web y también con la clave correcta). Para desbloquear al instante: `python manage.py axes_reset`.

## 2. Cómo enviar cada tipo de petición

- **Autorización:** pestaña Auth → Bearer Token → `{{TOKEN}}`. Equivale a la cabecera `Authorization: Bearer <token>`.
- **Cuerpo:** Body → raw → JSON (`Content-Type: application/json`). Sirve para POST, PUT y PATCH.
- Para guardar el token automáticamente en Postman, en la pestaña Tests del login:
  ```js
  pm.environment.set("TOKEN", pm.response.json().access);
  pm.environment.set("REFRESH", pm.response.json().refresh);
  ```
- Para guardar el id de la receta creada, en la pestaña Tests del POST de creación:
  ```js
  pm.environment.set("ID", pm.response.json().id);
  ```

## 3. Peticiones a probar (orden sugerido)

| # | Método y URL | Auth | Body | Esperado |
|---|---|---|---|---|
| 1 | POST `{{API}}/token/` | no | login de ana (ver sección 4) | 200, devuelve `access` y `refresh` |
| 2 | POST `{{API}}/token/` | no | `{"username":"ana","password":"incorrecta"}` | 401 (⚠️ cuenta para el bloqueo de 5) |
| 3 | POST `{{API}}/token/refresh/` | no | `{"refresh":"{{REFRESH}}"}` | 200, `access` y `refresh` nuevos |
| 4 | Repetir la 3 con el refresh anterior | no | el mismo refresh ya usado | 401 (revocado por la blacklist) |
| 5 | GET `{{API}}/recetas/` | no | — | 200, JSON con `count`, `next`, `previous`, `results` |
| 6 | GET `{{API}}/recetas/?page=2` | no | — | página siguiente (10 por página) |
| 7 | GET `{{API}}/recetas/{{ID}}/` | no | — | 200; 404 si no existe |
| 8 | POST `{{API}}/recetas/` | no | receta válida | **401** |
| 9 | POST `{{API}}/recetas/` | ana | receta válida | **201**, `autor` = ana |
| 10 | POST `{{API}}/recetas/` | ana | un solo ingrediente | 400, "al menos 2 ingredientes" |
| 11 | POST `{{API}}/recetas/` | ana | `tiempo_minutos` = 0 | 400 |
| 12 | POST `{{API}}/recetas/` | ana | `tiempo_minutos` = 5000 | 400 |
| 13 | POST `{{API}}/recetas/` | ana | `dificultad` = "imposible" | 400, opción no válida |
| 14 | POST `{{API}}/recetas/` | ana | sin `titulo` | 400 |
| 15 | POST `{{API}}/recetas/` | ana | con `"autor": "beto"` en el body | 201, pero `autor` = ana (se ignora) |
| 16 | PATCH `{{API}}/recetas/{{ID}}/` | ana | `{"titulo":"Editada"}` | 200 |
| 17 | PUT `{{API}}/recetas/{{ID}}/` | ana | todos los campos | 200 |
| 18 | PATCH `{{API}}/recetas/{{ID}}/` | beto | `{"titulo":"hack"}` sobre receta de ana | **403** |
| 19 | PUT `{{API}}/recetas/{{ID}}/` | beto | receta válida sobre receta de ana | **403** |
| 20 | DELETE `{{API}}/recetas/{{ID}}/` | beto | — (receta de ana) | **403** |
| 21 | GET `{{API}}/recetas/mios/` | ana | — | 200, solo las recetas de ana |
| 22 | GET `{{API}}/recetas/mios/` | beto | — | 200, solo las de beto |
| 23 | GET `{{API}}/recetas/mios/` | no | — | 401 |
| 24 | DELETE `{{API}}/recetas/{{ID}}/` | ana | — | 204 |
| 25 | GET `{{API}}/recetas/{{ID}}/` tras borrar | no | — | 404 |

## 4. Datos de prueba

### 4.1 Recetas válidas (para POST, esperado 201)

| # | `titulo` | `ingredientes` (uno por línea) | `preparacion` | `tiempo_minutos` | `dificultad` |
|---|---|---|---|---|---|
| V1 | Tortilla de papas | `3 huevos\n2 papas\nSal` | Freír las papas, mezclar con el huevo y cocinar. | 25 | `facil` |
| V2 | Cazuela de vacuno | `500 g de vacuno\n2 papas\n1 choclo\n1 zapallo` | Cocer todo a fuego lento por una hora. | 90 | `media` |
| V3 | Cordero al palo | `1 cordero\nSal\nPimienta` | Asar lentamente a la brasa durante horas. | 360 | `dificil` |
| V4 | Té con limón | `1 limón\n1 bolsita de té` | Infusionar y exprimir el limón. | 1 | `facil` |
| V5 | Fermentado largo | `Harina\nAgua\nMasa madre` | Reposar la masa por un día completo. | 1440 | `dificil` |

> En JSON, el salto de línea de los ingredientes se escribe `\n` dentro del texto.

### 4.2 Datos inválidos (esperado 400)

| # | Qué se prueba | Campo y valor | Mensaje esperado |
|---|---|---|---|
| I1 | Un solo ingrediente | `ingredientes`: `"solo uno"` | Escribe al menos 2 ingredientes, uno por línea. |
| I2 | Ingredientes vacíos entre líneas | `ingredientes`: `"uno\n\n   "` | Escribe al menos 2 ingredientes, uno por línea. |
| I3 | Tiempo cero | `tiempo_minutos`: `0` | Asegúrese de que este valor es mayor o igual a 1. |
| I4 | Tiempo sobre el máximo | `tiempo_minutos`: `1441` | Asegúrese de que este valor es menor o igual a 1440. |
| I5 | Tiempo negativo | `tiempo_minutos`: `-5` | Asegúrese de que este valor es mayor o igual a 1. |
| I6 | Tiempo no numérico | `tiempo_minutos`: `"rápido"` | Introduzca un número entero válido. |
| I7 | Dificultad inexistente | `dificultad`: `"imposible"` | "imposible" no es una elección válida. |
| I8 | Sin título | falta `titulo` | Este campo es requerido. |
| I9 | Título demasiado largo | `titulo`: 101 caracteres o más | Asegúrese de que este campo no tenga más de 100 caracteres. |
| I10 | Preparación gigante | `preparacion`: más de 10 000 caracteres | Asegúrese de que este valor tenga menos de 10000 caracteres (tiene 10001). |
| I11 | Ingredientes gigantes | `ingredientes`: más de 2000 caracteres | Asegúrese de que este valor tenga menos de 2000 caracteres (tiene N). |

> Los mensajes exactos los entrega Django en español (`LANGUAGE_CODE = es-cl`); los números entre paréntesis dependen de lo que envíes. Lo importante es el código **400** y que el error apunte al campo correcto.

### 4.3 Cuerpos JSON listos para pegar

Login de ana (petición 1):
```json
{
  "username": "ana",
  "password": "Ana-Recetas-2026"
}
```

Login de beto:
```json
{
  "username": "beto",
  "password": "Beto-Recetas-2026"
}
```

Crear receta (peticiones 8, 9 y 24; esperado 401 sin token y 201 con token):
```json
{
  "titulo": "Tortilla de papas",
  "ingredientes": "3 huevos\n2 papas\nSal",
  "preparacion": "Freír las papas, mezclar con el huevo y cocinar.",
  "tiempo_minutos": 25,
  "dificultad": "facil"
}
```

Un solo ingrediente, debe fallar con 400 (petición 10):
```json
{
  "titulo": "Mala",
  "ingredientes": "solo uno",
  "preparacion": "No importa.",
  "tiempo_minutos": 10,
  "dificultad": "facil"
}
```

Intento de falsificar el autor, debe quedar como ana (petición 15):
```json
{
  "titulo": "Autor falso",
  "ingredientes": "1 cosa\n2 cosas",
  "preparacion": "Probar que el servidor ignora el autor.",
  "tiempo_minutos": 5,
  "dificultad": "facil",
  "autor": "beto"
}
```

Reemplazo completo con PUT (petición 17):
```json
{
  "titulo": "Reemplazada",
  "ingredientes": "2 huevos\n1 taza de harina",
  "preparacion": "Mezclar y cocinar.",
  "tiempo_minutos": 15,
  "dificultad": "media"
}
```

## 5. Respuesta esperada de una receta

```json
{
  "id": 7,
  "titulo": "Tortilla de papas",
  "ingredientes": "3 huevos\n2 papas\nSal",
  "preparacion": "Freír las papas, mezclar con el huevo y cocinar.",
  "tiempo_minutos": 25,
  "dificultad": "facil",
  "autor": "ana",
  "creado": "2026-09-30T20:00:00.000000-03:00"
}
```

`autor` lo pone el servidor y `creado` también es de solo lectura: si los envías en el body se ignoran. Son exactamente 8 campos; si aparece alguno más, algo se expuso de más.

## 6. Códigos de estado que debes ver

| Código | Cuándo |
|---|---|
| 200 | Lectura o actualización correcta |
| 201 | Receta creada |
| 204 | Receta borrada (sin cuerpo) |
| 400 | Dato inválido (ver tabla 4.2) |
| 401 | Sin token, token vencido, login incorrecto o IP bloqueada por `axes` |
| 403 | Modificar o borrar una receta de otro usuario |
| 404 | La receta no existe |
| 429 | Demasiadas peticiones (throttling) |

## 7. Tests automáticos en Postman

En la pestaña Tests de cada petición:

```js
pm.test("código 201", () => pm.response.to.have.status(201));
pm.test("el autor es ana", () => pm.expect(pm.response.json().autor).to.eql("ana"));
pm.test("8 campos exactos", () => pm.expect(Object.keys(pm.response.json())).to.have.lengthOf(8));
```

Con el Collection Runner ejecutas toda la colección en orden y obtienes un reporte. Puedes exportar la colección como evidencia para la entrega.

## 8. Probar el límite de peticiones (throttling)

Anónimos: 30 por minuto. Autenticados: 120 por minuto. Con el Collection Runner, repite el GET `{{API}}/recetas/` más de 30 veces en un minuto sin token: las últimas respuestas deben ser **429**. Espera un minuto para recuperar el acceso. El límite también cuenta para `/api/token/`.

## 9. Probar el bloqueo por logins fallidos (django-axes)

1. Repite la petición 2 cinco veces: las cinco dan 401.
2. Haz login con la clave **correcta**: también da 401 (la IP está bloqueada 15 minutos).
3. Desbloquea con `python manage.py axes_reset` y repite la petición 1: vuelve a dar 200.

## 10. Inspeccionar el JWT

Pega el `access` en jwt.io para ver `exp` (vencimiento), `user_id` y `token_type`. No pegues tokens de un entorno real.

## 11. Lo que este cliente no cubre

- **Web HTML:** los formularios con CSRF, el login por sesión, el dashboard y la configuración no se prueban aquí; los cubren los 15 tests de `recetas/tests.py`.
- **CORS:** estos clientes no lo aplican; solo lo aplica un navegador.

## 12. Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| 401 con token | El `access` venció (30 min): pide uno nuevo con el login o el refresh. |
| 401 al renovar | El refresh ya se usó (rota en cada uso) o venció (1 día). Haz login otra vez. |
| 401 con la clave correcta | Tu IP quedó bloqueada por `axes` tras 5 fallos: espera 15 min o ejecuta `python manage.py axes_reset`. |
| 403 al editar | La receta es de otro usuario; usa el token del autor. |
| 400 en una receta "normal" | Revisa que `ingredientes` tenga al menos 2 líneas (`\n` entre ellas) y que `dificultad` sea `facil`, `media` o `dificil`. |
| 429 | Esperar un minuto. |
| No conecta | El servidor no está levantado o el puerto no es el 8000. |
