from django import forms

from .models import Receta


class RecetaForm(forms.ModelForm):
    # Las validaciones del modelo (ingredientes, tiempo 1-1440) corren solas aqui.
    class Meta:
        model = Receta
        fields = ["titulo", "ingredientes", "preparacion", "tiempo_minutos", "dificultad"]

    def clean_titulo(self):
        titulo = self.cleaned_data["titulo"].strip()
        if len(titulo) < 3:
            raise forms.ValidationError("El título debe tener al menos 3 caracteres.")
        return titulo
