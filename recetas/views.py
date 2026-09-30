from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import RecetaForm
from .models import Receta


class SoloAutorMixin(UserPassesTestMixin):
    """Editar o borrar solo si el usuario es el autor (si no, 403)."""

    def test_func(self):
        return self.get_object().autor == self.request.user


class RecetaListView(ListView):
    model = Receta
    paginate_by = 12

    def get_queryset(self):
        return Receta.objects.select_related("autor")


class RecetaDetailView(DetailView):
    model = Receta


class RecetaCreateView(LoginRequiredMixin, CreateView):
    model = Receta
    form_class = RecetaForm

    def form_valid(self, form):
        form.instance.autor = self.request.user  # el autor lo pone el servidor
        return super().form_valid(form)


class RecetaUpdateView(LoginRequiredMixin, SoloAutorMixin, UpdateView):
    model = Receta
    form_class = RecetaForm


class RecetaDeleteView(LoginRequiredMixin, SoloAutorMixin, DeleteView):
    model = Receta
    success_url = reverse_lazy("recetas:lista")


class RegistroView(CreateView):
    form_class = UserCreationForm
    template_name = "registration/registro.html"
    success_url = reverse_lazy("recetas:lista")

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        # con varios backends (axes + ModelBackend) hay que indicar cual usar
        login(self.request, self.object, backend="django.contrib.auth.backends.ModelBackend")
        return respuesta
