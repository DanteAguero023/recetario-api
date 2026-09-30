from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg, Count
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

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
    success_url = reverse_lazy("recetas:dashboard")

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        # con varios backends (axes + ModelBackend) hay que indicar cual usar
        login(self.request, self.object, backend="django.contrib.auth.backends.ModelBackend")
        return respuesta


class DashboardView(LoginRequiredMixin, TemplateView):
    """Resumen personal: mis cifras, reparto por dificultad y ultimas recetas."""

    template_name = "recetas/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        mias = Receta.objects.filter(autor=self.request.user)
        total = mias.count()
        conteo = dict(mias.values_list("dificultad").annotate(n=Count("id")))
        ctx["total_mias"] = total
        ctx["total_comunidad"] = Receta.objects.count()
        ctx["tiempo_promedio"] = round(mias.aggregate(p=Avg("tiempo_minutos"))["p"] or 0)
        ctx["por_dificultad"] = [
            {
                "etiqueta": etiqueta,
                "clave": clave,
                "n": conteo.get(clave, 0),
                "pct": round(conteo.get(clave, 0) * 100 / total) if total else 0,
            }
            for clave, etiqueta in Receta.Dificultad.choices
        ]
        ctx["ultimas"] = mias[:5]
        return ctx


class ConfiguracionView(LoginRequiredMixin, TemplateView):
    """Preferencias de interfaz (se guardan en el navegador) y acceso a la cuenta."""

    template_name = "recetas/configuracion.html"
