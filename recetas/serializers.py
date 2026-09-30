from rest_framework import serializers

from .models import Receta


class RecetaSerializer(serializers.ModelSerializer):
    # el autor lo pone el servidor: se muestra, no se recibe
    autor = serializers.ReadOnlyField(source="autor.username")

    class Meta:
        model = Receta
        # explicitos, nunca "__all__": lo que no se lista, no se expone
        fields = ["id", "titulo", "ingredientes", "preparacion", "tiempo_minutos", "dificultad", "autor", "creado"]
        read_only_fields = ["creado"]
    # Las reglas del modelo (ingredientes >= 2, tiempo 1-1440) las aplica DRF solo,
    # asi la API y la web validan exactamente lo mismo.
