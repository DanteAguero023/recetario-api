from django.core.exceptions import ValidationError


def validar_ingredientes(texto):
    """Regla propia: una receta necesita al menos 2 ingredientes (uno por linea).

    Va en el modelo, asi la aplican igual la web (ModelForm) y la API (Serializer).
    """
    lineas = [linea for linea in texto.splitlines() if linea.strip()]
    if len(lineas) < 2:
        raise ValidationError("Escribe al menos 2 ingredientes, uno por línea.")
