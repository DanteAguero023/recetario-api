from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Receta

DATOS = {
    "titulo": "Tortilla",
    "ingredientes": "3 huevos\n1 papa",
    "preparacion": "Batir y cocinar.",
    "tiempo_minutos": 15,
    "dificultad": "facil",
}


class WebTest(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user("ana", password="clave-ana-123")
        self.beto = User.objects.create_user("beto", password="clave-beto-123")
        self.receta = Receta.objects.create(autor=self.ana, **DATOS)

    def test_lista_y_detalle_publicos(self):
        self.assertEqual(self.client.get(reverse("recetas:lista")).status_code, 200)
        self.assertEqual(self.client.get(self.receta.get_absolute_url()).status_code, 200)

    def test_crear_exige_login(self):
        r = self.client.get(reverse("recetas:crear"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/cuentas/login/", r.url)

    def test_crear_asigna_autor(self):
        self.client.force_login(self.beto)
        r = self.client.post(reverse("recetas:crear"), {**DATOS, "titulo": "De Beto"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Receta.objects.get(titulo="De Beto").autor, self.beto)

    def test_validacion_ingredientes(self):
        self.client.force_login(self.ana)
        r = self.client.post(reverse("recetas:crear"), {**DATOS, "ingredientes": "solo uno"})
        self.assertEqual(r.status_code, 200)  # vuelve al formulario con el error
        self.assertFalse(Receta.objects.filter(ingredientes="solo uno").exists())

    def test_validacion_tiempo(self):
        self.client.force_login(self.ana)
        r = self.client.post(reverse("recetas:crear"), {**DATOS, "tiempo_minutos": 0})
        self.assertEqual(r.status_code, 200)

    def test_autor_edita(self):
        self.client.force_login(self.ana)
        r = self.client.post(reverse("recetas:editar", args=[self.receta.pk]), {**DATOS, "titulo": "Nueva"})
        self.assertEqual(r.status_code, 302)
        self.receta.refresh_from_db()
        self.assertEqual(self.receta.titulo, "Nueva")

    def test_ajeno_no_edita_ni_borra_403(self):
        self.client.force_login(self.beto)
        self.assertEqual(self.client.get(reverse("recetas:editar", args=[self.receta.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("recetas:borrar", args=[self.receta.pk])).status_code, 403)
        self.assertTrue(Receta.objects.filter(pk=self.receta.pk).exists())

    def test_autor_borra(self):
        self.client.force_login(self.ana)
        self.client.post(reverse("recetas:borrar", args=[self.receta.pk]))
        self.assertFalse(Receta.objects.filter(pk=self.receta.pk).exists())

    def test_registro_login_logout(self):
        r = self.client.post(reverse("recetas:registro"), {
            "username": "carla", "password1": "una-clave-larga-987", "password2": "una-clave-larga-987",
        })
        self.assertEqual(r.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)  # quedo logueada
        self.client.post(reverse("logout"))
        self.assertNotIn("_auth_user_id", self.client.session)
        r = self.client.post(reverse("login"), {"username": "carla", "password": "una-clave-larga-987"})
        self.assertEqual(r.status_code, 302)  # el login web sigue funcionando con axes
        self.assertIn("_auth_user_id", self.client.session)


class DashboardYConfiguracionTest(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user("ana", password="clave-ana-123")
        self.beto = User.objects.create_user("beto", password="clave-beto-123")
        Receta.objects.create(autor=self.ana, **{**DATOS, "tiempo_minutos": 10})
        Receta.objects.create(autor=self.ana, **{**DATOS, "titulo": "Otra", "tiempo_minutos": 30, "dificultad": "media"})
        Receta.objects.create(autor=self.beto, **{**DATOS, "titulo": "De Beto"})

    def test_exigen_login(self):
        for nombre in ("recetas:dashboard", "recetas:configuracion"):
            r = self.client.get(reverse(nombre))
            self.assertEqual(r.status_code, 302)
            self.assertIn("/cuentas/login/", r.url)

    def test_dashboard_cuenta_solo_lo_mio(self):
        self.client.force_login(self.ana)
        r = self.client.get(reverse("recetas:dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["total_mias"], 2)
        self.assertEqual(r.context["total_comunidad"], 3)
        self.assertEqual(r.context["tiempo_promedio"], 20)  # (10 + 30) / 2
        reparto = {d["clave"]: d["pct"] for d in r.context["por_dificultad"]}
        self.assertEqual(reparto, {"facil": 50, "media": 50, "dificil": 0})

    def test_dashboard_sin_recetas(self):
        nueva = User.objects.create_user("nueva", password="clave-nueva-123")
        self.client.force_login(nueva)
        r = self.client.get(reverse("recetas:dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["total_mias"], 0)
        self.assertEqual(r.context["tiempo_promedio"], 0)

    def test_configuracion_y_cambio_de_clave(self):
        self.client.force_login(self.ana)
        self.assertEqual(self.client.get(reverse("recetas:configuracion")).status_code, 200)
        self.assertEqual(self.client.get(reverse("password_change")).status_code, 200)

    def test_login_redirige_al_dashboard(self):
        r = self.client.post(reverse("login"), {"username": "ana", "password": "clave-ana-123"})
        self.assertRedirects(r, reverse("recetas:dashboard"))

    def test_estaticos_referenciados(self):
        r = self.client.get(reverse("recetas:lista"))
        self.assertContains(r, "recetas/styles.css")
        self.assertContains(r, 'id="splash"')
