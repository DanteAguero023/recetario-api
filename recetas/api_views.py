from rest_framework import permissions, viewsets
from rest_framework.decorators import action

from .models import Receta
from .permissions import EsAutorOSoloLectura
from .serializers import RecetaSerializer


class RecetaViewSet(viewsets.ModelViewSet):
    queryset = Receta.objects.select_related("autor")
    serializer_class = RecetaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, EsAutorOSoloLectura]

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

    @action(detail=False, permission_classes=[permissions.IsAuthenticated])
    def mios(self, request):
        """GET /api/recetas/mios/ -> solo las recetas del usuario del token."""
        qs = self.get_queryset().filter(autor=request.user)
        pagina = self.paginate_queryset(qs)
        return self.get_paginated_response(self.get_serializer(pagina, many=True).data)
