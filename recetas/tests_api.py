from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from .models import Receta

DATOS = {
    "titulo": "Tortilla",
    "ingredientes": "3 huevos\n1 papa",
    "preparacion": "Batir y cocinar.",
    "tiempo_minutos": 15,
    "dificultad": "facil",
}


class CandadoApiTest(APITestCase):
    def setUp(self):
        self.ana = User.objects.create_user("ana", password="clave-ana-123")
        self.beto = User.objects.create_user("beto", password="clave-beto-123")
        self.receta = Receta.objects.create(autor=self.ana, **DATOS)

    def test_listar_200_paginado(self):
        r = self.client.get("/api/recetas/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["count"], 1)
        self.assertIn("results", r.data)

    def test_sin_token_no_crea_401(self):
        self.assertEqual(self.client.post("/api/recetas/", DATOS).status_code, 401)

    def test_token_jwt_y_crear_201(self):
        r = self.client.post("/api/token/", {"username": "ana", "password": "clave-ana-123"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("access", r.data)
        self.assertIn("refresh", r.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
        r = self.client.post("/api/recetas/", DATOS)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["autor"], "ana")

    def test_autor_del_cliente_se_ignora(self):
        self.client.force_authenticate(self.ana)
        r = self.client.post("/api/recetas/", {**DATOS, "autor": "beto"})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["autor"], "ana")  # manda el servidor, no el cliente

    def test_campos_expuestos_explicitos(self):
        r = self.client.get(f"/api/recetas/{self.receta.pk}/")
        self.assertEqual(
            set(r.data),
            {"id", "titulo", "ingredientes", "preparacion", "tiempo_minutos", "dificultad", "autor", "creado"},
        )

    def test_validaciones_400(self):
        self.client.force_authenticate(self.ana)
        self.assertEqual(self.client.post("/api/recetas/", {**DATOS, "ingredientes": "uno"}).status_code, 400)
        self.assertEqual(self.client.post("/api/recetas/", {**DATOS, "tiempo_minutos": 5000}).status_code, 400)
        self.assertEqual(self.client.post("/api/recetas/", {**DATOS, "preparacion": "x" * 10001}).status_code, 400)

    def test_ajeno_403_en_put_patch_delete(self):
        self.client.force_authenticate(self.beto)
        url = f"/api/recetas/{self.receta.pk}/"
        self.assertEqual(self.client.put(url, DATOS).status_code, 403)
        self.assertEqual(self.client.patch(url, {"titulo": "x"}).status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.assertTrue(Receta.objects.filter(pk=self.receta.pk).exists())

    def test_autor_actualiza_y_borra(self):
        self.client.force_authenticate(self.ana)
        url = f"/api/recetas/{self.receta.pk}/"
        self.assertEqual(self.client.patch(url, {"titulo": "Nuevo"}).status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_mios_solo_del_usuario(self):
        self.client.force_authenticate(self.ana)
        self.assertEqual(self.client.get("/api/recetas/mios/").data["count"], 1)
        self.client.force_authenticate(self.beto)
        self.assertEqual(self.client.get("/api/recetas/mios/").data["count"], 0)

    def test_mios_requiere_token(self):
        self.assertEqual(self.client.get("/api/recetas/mios/").status_code, 401)


class RefreshRotadoTest(APITestCase):
    def test_refresh_usado_queda_revocado(self):
        User.objects.create_user("ana", password="clave-ana-123")
        r = self.client.post("/api/token/", {"username": "ana", "password": "clave-ana-123"})
        viejo = r.data["refresh"]
        r1 = self.client.post("/api/token/refresh/", {"refresh": viejo})
        self.assertEqual(r1.status_code, 200)
        self.assertIn("refresh", r1.data)
        self.assertEqual(self.client.post("/api/token/refresh/", {"refresh": viejo}).status_code, 401)


class ThrottlingTest(APITestCase):
    def test_anonimo_excedido_recibe_429(self):
        from django.core.cache import cache
        cache.clear()
        codigos = [self.client.get("/api/recetas/").status_code for _ in range(31)]
        self.assertEqual(codigos[:30], [200] * 30)
        self.assertEqual(codigos[30], 429)
        cache.clear()

    def test_login_por_fuerza_bruta_tambien_limitado(self):
        from django.core.cache import cache
        cache.clear()
        malo = {"username": "ana", "password": "incorrecta"}
        codigos = [self.client.post("/api/token/", malo).status_code for _ in range(31)]
        self.assertEqual(codigos[-1], 429)  # el intento 31 del minuto se corta
        cache.clear()


class BloqueoLoginTest(APITestCase):
    def test_cinco_fallos_bloquean_aunque_luego_venga_la_clave_correcta(self):
        from django.core.cache import cache
        cache.clear()
        User.objects.create_user("ana", password="clave-ana-123")
        for _ in range(5):
            r = self.client.post("/api/token/", {"username": "ana", "password": "mala"})
            self.assertEqual(r.status_code, 401)
        r = self.client.post("/api/token/", {"username": "ana", "password": "clave-ana-123"})
        self.assertEqual(r.status_code, 401)  # bloqueada por axes: ni con la clave correcta
        self.assertNotIn("access", r.data)
        cache.clear()
