/* ═══════════════════════════════════════════════════════════════════════
   Selector de tema: un botón arriba a la derecha que abre la lista de
   temas con su nombre. El elegido se guarda en este navegador.

   Los colores y los efectos de cada tema están en taller.css; acá solo
   van el nombre y la muestra que se ve en la lista.
   ═══════════════════════════════════════════════════════════════════════ */

(function () {
  "use strict";

  var TEMAS = [
    {id: "neon",     nombre: "Neón",     nota: "bordes que brillan",   muestra: "linear-gradient(135deg,#0A0618 50%,#22E3FF 50%)"},
    {id: "matrix",   nombre: "Matrix",   nota: "verde sobre negro",    muestra: "linear-gradient(135deg,#000400 50%,#00FF41 50%)"},
    {id: "terminal", nombre: "Terminal", nota: "consola con prompt",   muestra: "linear-gradient(135deg,#05090A 50%,#2BE58B 50%)"},
    {id: "crt",      nombre: "CRT",      nota: "fósforo ámbar",        muestra: "linear-gradient(135deg,#0B0703 50%,#FFA023 50%)"},
    {id: "tecnico",  nombre: "Técnico",  nota: "sobrio, sin adornos",  muestra: "linear-gradient(135deg,#FFFFFF 50%,#12674A 50%)"},
    {id: "nord",     nombre: "Nord",     nota: "azules fríos",         muestra: "linear-gradient(135deg,#2E3440 50%,#88C0D0 50%)"},
    {id: "papel",    nombre: "Papel",    nota: "claro y cálido",       muestra: "linear-gradient(135deg,#F6F1E6 50%,#7A5C2E 50%)"},
    {id: "",         nombre: "Editor",   nota: "sigue al sistema",     muestra: "linear-gradient(135deg,#F4F5F1 50%,#0D1117 50%)"}
  ];

  var CLAVE = "taller.tema";
  var PREDETERMINADO = "neon";
  var opciones = [];

  function guardado() {
    try {
      var v = localStorage.getItem(CLAVE);
      return v === null ? PREDETERMINADO : v;
    } catch (e) { return PREDETERMINADO; }
  }

  function aplicar(id) {
    if (id) document.documentElement.setAttribute("data-tema", id);
    else document.documentElement.removeAttribute("data-tema");
    try { localStorage.setItem(CLAVE, id); } catch (e) {}
    marcar(id);
  }

  function marcar(id) {
    opciones.forEach(function (o) {
      o.setAttribute("aria-current", o.dataset.tema === id ? "true" : "false");
    });
  }

  // Se aplica antes de dibujar la lista, para que no se vea el cambio de color.
  aplicar(guardado());

  function armar() {
    var caja = document.createElement("div");
    caja.className = "temas";

    var boton = document.createElement("button");
    boton.type = "button";
    boton.className = "temas-boton";
    boton.setAttribute("aria-haspopup", "true");
    boton.setAttribute("aria-expanded", "false");
    boton.title = "Cambiar el tema";
    var rueda = document.createElement("span");
    rueda.className = "rueda";
    boton.appendChild(rueda);
    boton.setAttribute("aria-label", "Cambiar el tema");

    var lista = document.createElement("ul");
    lista.className = "temas-lista";
    lista.hidden = true;

    TEMAS.forEach(function (t) {
      var li = document.createElement("li");
      var b = document.createElement("button");
      b.type = "button";
      b.dataset.tema = t.id;

      var m = document.createElement("span");
      m.className = "muestra";
      m.style.background = t.muestra;

      var n = document.createElement("span");
      n.textContent = t.nombre + " · " + t.nota;

      var tilde = document.createElement("span");
      tilde.className = "tilde";
      tilde.textContent = "✓";

      b.appendChild(m);
      b.appendChild(n);
      b.appendChild(tilde);
      b.addEventListener("click", function () {
        aplicar(t.id);
        cerrar();
      });
      li.appendChild(b);
      lista.appendChild(li);
      opciones.push(b);
    });

    function abrir() {
      lista.hidden = false;
      boton.setAttribute("aria-expanded", "true");
      document.addEventListener("click", afuera, true);
      document.addEventListener("keydown", conEscape);
    }
    function cerrar() {
      lista.hidden = true;
      boton.setAttribute("aria-expanded", "false");
      document.removeEventListener("click", afuera, true);
      document.removeEventListener("keydown", conEscape);
    }
    function afuera(ev) { if (!caja.contains(ev.target)) cerrar(); }
    function conEscape(ev) { if (ev.key === "Escape") cerrar(); }

    boton.addEventListener("click", function (ev) {
      ev.stopPropagation();
      if (lista.hidden) abrir(); else cerrar();
    });

    caja.appendChild(boton);
    caja.appendChild(lista);
    document.body.appendChild(caja);
    marcar(guardado());
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", armar);
  } else {
    armar();
  }
})();
