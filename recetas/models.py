from django.conf import settings
from django.core.validators import MaxLengthValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

from .validators import validar_ingredientes


class Receta(models.Model):
    class Dificultad(models.TextChoices):
        FACIL = "facil", "Fácil"
        MEDIA = "media", "Media"
        DIFICIL = "dificil", "Difícil"

    titulo = models.CharField(max_length=100)
    # tope de tamaño: evita cuerpos gigantes (OWASP API4, consumo de recursos)
    ingredientes = models.TextField(
        validators=[validar_ingredientes, MaxLengthValidator(2000)], help_text="Uno por línea."
    )
    preparacion = models.TextField(validators=[MaxLengthValidator(10000)])
    tiempo_minutos = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(1440)],
        help_text="Entre 1 y 1440 minutos.",
    )
    dificultad = models.CharField(max_length=10, choices=Dificultad.choices, default=Dificultad.FACIL)
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recetas")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse("recetas:detalle", args=[self.pk])
