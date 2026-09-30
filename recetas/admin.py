from django.contrib import admin

from .models import Receta


@admin.register(Receta)
class RecetaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "autor", "dificultad", "tiempo_minutos", "creado")
    list_filter = ("dificultad", "autor")
    search_fields = ("titulo", "ingredientes")
