from rest_framework import permissions


class EsAutorOSoloLectura(permissions.BasePermission):
    """Todos leen. Solo el autor modifica o borra su receta."""

    message = "Solo el autor puede modificar esta receta."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:  # GET, HEAD, OPTIONS
            return True
        return obj.autor == request.user
