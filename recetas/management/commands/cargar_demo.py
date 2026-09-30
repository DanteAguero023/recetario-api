from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from recetas.models import Receta

CLAVES = {"ana": "Ana-Recetas-2026", "beto": "Beto-Recetas-2026"}

DEMO = {
    "ana": [
        ("Panqueques", "2 huevos\n1 taza de harina\n1 taza de leche", "Mezclar todo y cocinar en sartén caliente.", 20, "facil"),
        ("Pastel de choclo", "6 choclos\n500 g de carne molida\n2 cebollas\n1 pollo", "Preparar el pino, cubrir con pastelera y hornear.", 90, "media"),
    ],
    "beto": [
        ("Completo italiano", "4 panes\n4 vienesas\n2 tomates\n1 palta", "Armar el pan con los ingredientes y servir.", 15, "facil"),
    ],
}


class Command(BaseCommand):
    help = "Crea (o actualiza) los usuarios demo ana y beto con recetas de ejemplo."

    def handle(self, *args, **opts):
        for nombre, recetas in DEMO.items():
            usuario, _ = User.objects.get_or_create(username=nombre)
            usuario.set_password(CLAVES[nombre])  # tambien actualiza usuarios ya existentes
            usuario.save()
            for titulo, ingredientes, preparacion, minutos, dificultad in recetas:
                Receta.objects.get_or_create(
                    titulo=titulo,
                    autor=usuario,
                    defaults=dict(ingredientes=ingredientes, preparacion=preparacion, tiempo_minutos=minutos, dificultad=dificultad),
                )
        self.stdout.write(self.style.SUCCESS("Datos demo listos: ana / Ana-Recetas-2026 y beto / Beto-Recetas-2026."))
