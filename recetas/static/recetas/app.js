/* Mi Recetario · comportamiento del front
   - Preferencias (tema, animaciones, tamano, splash) guardadas en localStorage.
   - Splash de bienvenida una vez por sesion del navegador (y de nuevo al ingresar).
   El bloque que aplica las preferencias antes de pintar esta inline en base.html. */
(function () {
  "use strict";
  var raiz = document.documentElement;
  var CLAVES = { tema: "rc-tema", anim: "rc-anim", tam: "rc-tam", splash: "rc-splash" };

  function leer(k, def) { try { return localStorage.getItem(k) || def; } catch (e) { return def; } }
  function guardar(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* modo privado: se ignora */ } }

  function aplicar() {
    var tema = leer(CLAVES.tema, "auto");
    if (tema === "auto") raiz.removeAttribute("data-theme"); else raiz.setAttribute("data-theme", tema);
    raiz.setAttribute("data-anim", leer(CLAVES.anim, "on"));
    raiz.setAttribute("data-size", leer(CLAVES.tam, "normal"));
  }

  /* ---- Splash ---- */
  function cerrarSplash() {
    var s = document.getElementById("splash");
    if (!s || s.classList.contains("saliendo")) return;
    s.classList.add("saliendo");
    try { sessionStorage.setItem("rc-splash-visto", "1"); } catch (e) { /* ignorar */ }
    setTimeout(function () { raiz.classList.remove("splash-on"); }, 750);
  }
  function iniciarSplash() {
    var s = document.getElementById("splash");
    if (!s || !raiz.classList.contains("splash-on")) return;
    s.addEventListener("click", cerrarSplash);
    document.addEventListener("keydown", cerrarSplash, { once: true });
    setTimeout(cerrarSplash, 2300);
  }
  // al ingresar, registrarse o salir, el proximo inicio vuelve a mostrar el splash
  function reprogramarSplash() {
    document.querySelectorAll("form[data-splash-reset]").forEach(function (f) {
      f.addEventListener("submit", function () {
        try { sessionStorage.removeItem("rc-splash-visto"); } catch (e) { /* ignorar */ }
      });
    });
  }

  /* ---- Toast ---- */
  var temporizador;
  function aviso(texto) {
    var t = document.getElementById("toast");
    if (!t) return;
    t.textContent = texto;
    t.classList.add("visible");
    clearTimeout(temporizador);
    temporizador = setTimeout(function () { t.classList.remove("visible"); }, 1800);
  }

  /* ---- Pagina de configuraciones ---- */
  function iniciarAjustes() {
    var panel = document.getElementById("ajustes");
    if (!panel) return;
    var campos = {
      tema: panel.querySelectorAll('input[name="tema"]'),
      tam: panel.querySelectorAll('input[name="tam"]'),
      anim: panel.querySelector('input[name="anim"]'),
      splash: panel.querySelector('input[name="splash"]')
    };
    function pintar() {
      campos.tema.forEach(function (r) { r.checked = r.value === leer(CLAVES.tema, "auto"); });
      campos.tam.forEach(function (r) { r.checked = r.value === leer(CLAVES.tam, "normal"); });
      campos.anim.checked = leer(CLAVES.anim, "on") === "on";
      campos.splash.checked = leer(CLAVES.splash, "on") === "on";
    }
    campos.tema.forEach(function (r) { r.addEventListener("change", function () { guardar(CLAVES.tema, r.value); aplicar(); aviso("Tema guardado"); }); });
    campos.tam.forEach(function (r) { r.addEventListener("change", function () { guardar(CLAVES.tam, r.value); aplicar(); aviso("Tamaño guardado"); }); });
    campos.anim.addEventListener("change", function () { guardar(CLAVES.anim, campos.anim.checked ? "on" : "off"); aplicar(); aviso(campos.anim.checked ? "Animaciones activadas" : "Animaciones desactivadas"); });
    campos.splash.addEventListener("change", function () { guardar(CLAVES.splash, campos.splash.checked ? "on" : "off"); aviso(campos.splash.checked ? "Splash activado" : "Splash desactivado"); });
    var reset = document.getElementById("restablecer");
    if (reset) reset.addEventListener("click", function () {
      Object.keys(CLAVES).forEach(function (k) { try { localStorage.removeItem(CLAVES[k]); } catch (e) { /* ignorar */ } });
      aplicar(); pintar(); aviso("Preferencias restablecidas");
    });
    var verSplash = document.getElementById("ver-splash");
    if (verSplash) verSplash.addEventListener("click", function () {
      try { sessionStorage.removeItem("rc-splash-visto"); } catch (e) { /* ignorar */ }
      var s = document.getElementById("splash");
      if (!s) return;
      s.classList.remove("saliendo");
      raiz.classList.add("splash-on");
      iniciarSplash();
    });
    pintar();
  }

  /* ---- Escalonar la entrada de elementos .aparece ---- */
  function escalonar() {
    document.querySelectorAll("[data-stagger]").forEach(function (grupo) {
      grupo.querySelectorAll(".aparece").forEach(function (el, i) { el.style.setProperty("--i", Math.min(i, 12)); });
    });
  }

  aplicar();
  document.addEventListener("DOMContentLoaded", function () {
    escalonar();
    reprogramarSplash();
    iniciarSplash();
    iniciarAjustes();
  });
})();
