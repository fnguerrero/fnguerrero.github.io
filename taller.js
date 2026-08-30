/* ═══════════════════════════════════════════════════════════════════════
   El taller: filas de portadas y ficha de detalle.

   Lo usan las dos páginas, index.html (la pública) y home.html (la del
   navegador), para que se vean y se comporten igual. Los datos salen
   siempre de proyectos.json; esto solo los dibuja.

   API:
     Taller.filas(contenedor, grupos, opciones)
     Taller.ficha(proyecto, verbo)
   Opciones:
     base   prefijo para las imágenes (la home las pide a GitHub)
     extras cartas propias de la máquina (con puerto y lucecita)
   ═══════════════════════════════════════════════════════════════════════ */

var Taller = (function () {
  "use strict";

  var base = "";

  function el(tag, clase, texto) {
    var e = document.createElement(tag);
    if (clase) e.className = clase;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }

  function enlace(clase, href, texto) {
    var a = el("a", clase, texto);
    a.href = href;
    a.target = "_blank";
    a.rel = "noopener";
    return a;
  }

  // Los datos pueden venir de un archivo remoto: los links se revisan antes de
  // usarlos. Solo https:// y http://localhost; lo demás no se pinta como link.
  function linkSeguro(url) {
    if (!url) return null;
    try {
      var u = new URL(url, location.href);
      if (u.protocol === "https:") return u.href;
      if (u.protocol === "http:" && (u.hostname === "localhost" || u.hostname === "127.0.0.1")) {
        return u.href;
      }
    } catch (e) {}
    return null;
  }

  function imagenes(p) {
    var lista = [];
    if (p.imgs && p.imgs.length) lista = p.imgs.slice();
    else if (p.img) lista = [p.img];
    return lista.map(function (i) {
      return /^https?:/i.test(i) ? i : base + i;
    });
  }

  /* ───────── ficha ───────── */

  var dlg, gal, grande, puntos, izq, der, fotos = [], actual = 0;

  function armarDialogo() {
    dlg = document.getElementById("detalle");
    if (dlg) return;

    dlg = document.createElement("dialog");
    dlg.id = "detalle";
    dlg.innerHTML =
      '<div class="ficha">' +
        '<div class="galeria">' +
          '<img class="grande" alt="">' +
          '<button class="paso izq" type="button" title="Anterior">‹</button>' +
          '<button class="paso der" type="button" title="Siguiente">›</button>' +
          '<div class="puntos"></div>' +
        '</div>' +
        '<div class="texto">' +
          '<h2></h2><span class="tag"></span><p></p>' +
          '<div class="chips"></div><div class="acciones"></div>' +
        '</div>' +
      '</div>';
    document.body.appendChild(dlg);

    gal = dlg.querySelector(".galeria");
    grande = dlg.querySelector(".grande");
    puntos = dlg.querySelector(".puntos");
    izq = dlg.querySelector(".paso.izq");
    der = dlg.querySelector(".paso.der");

    izq.addEventListener("click", function () { mostrar(actual - 1); });
    der.addEventListener("click", function () { mostrar(actual + 1); });
    dlg.addEventListener("click", function (ev) { if (ev.target === dlg) dlg.close(); });
    document.addEventListener("keydown", function (ev) {
      if (!dlg.open || fotos.length < 2) return;
      if (ev.key === "ArrowRight") mostrar(actual + 1);
      if (ev.key === "ArrowLeft") mostrar(actual - 1);
    });
  }

  function mostrar(i) {
    if (!fotos.length) return;
    actual = (i + fotos.length) % fotos.length;
    grande.src = fotos[actual];
    Array.prototype.forEach.call(puntos.children, function (b, n) {
      b.classList.toggle("activo", n === actual);
    });
  }

  function ficha(p, verbo) {
    armarDialogo();

    fotos = imagenes(p);
    var varias = fotos.length > 1;
    gal.style.display = fotos.length ? "" : "none";
    izq.style.display = der.style.display = varias ? "" : "none";

    puntos.textContent = "";
    if (varias) {
      fotos.forEach(function (_, n) {
        var b = document.createElement("b");
        b.addEventListener("click", function () { mostrar(n); });
        puntos.appendChild(b);
      });
    }
    mostrar(0);
    grande.alt = "Captura de " + p.nombre;

    dlg.querySelector("h2").textContent = p.nombre;
    dlg.querySelector(".tag").textContent = p.tag || "";
    dlg.querySelector(".texto p").textContent = p.que || "";

    var chips = dlg.querySelector(".chips");
    chips.textContent = "";
    (p.chips || []).forEach(function (c) { chips.appendChild(el("span", "chip", c)); });

    var acc = dlg.querySelector(".acciones");
    acc.textContent = "";
    var url = linkSeguro(p.url);
    if (url) acc.appendChild(enlace("btn", url, verbo || "Abrir"));
    var repo = linkSeguro(p.repo);
    if (repo) acc.appendChild(enlace("btn suave", repo, "Código"));
    var x = el("button", "cerrar", "cerrar");
    x.addEventListener("click", function () { dlg.close(); });
    acc.appendChild(x);

    dlg.showModal();
  }

  /* ───────── tarjetas y filas ───────── */

  function carta(p, verbo) {
    // Es un div y no un button porque adentro va un link ("Abrir"), y un link
    // dentro de un boton no es HTML valido.
    var b = el("div", "carta");
    b.tabIndex = 0;
    b.setAttribute("role", "button");

    var marco = el("div", "marco");
    var fotos = imagenes(p);
    if (fotos.length) {
      var img = document.createElement("img");
      img.src = fotos[0];
      img.alt = "Portada de " + p.nombre;
      img.loading = "lazy";
      marco.appendChild(img);
    } else {
      // Sin portada (las APIs, por ejemplo): la sigla sobre el color del proyecto.
      var sinfoto = el("div", "sinfoto", p.sigla || "");
      if (p.color) sinfoto.style.setProperty("--c", p.color);
      marco.appendChild(sinfoto);
    }

    // El boton "Abrir" del velo lleva derecho a la app; el resto de la tarjeta
    // abre la ficha con la descripcion y las capturas.
    var directo = linkSeguro(p.url);
    if (directo) {
      var velo = el("div", "velo");
      var ir = enlace(null, directo, verbo || "Abrir");
      ir.addEventListener("click", function (ev) { ev.stopPropagation(); });
      velo.appendChild(ir);
      marco.appendChild(velo);
    }

    var pie = el("div", "pie");
    pie.appendChild(el("b", null, p.nombre));
    if (p.tag) pie.appendChild(el("i", null, p.tag));
    // Punto verde = se puede abrir ahora. Lo que esta en internet siempre lo
    // esta; lo que corre en esta maquina, solo si el servidor responde (de eso
    // se encarga home.html, que despues prende la luz).
    if (directo) {
      var luz = el("span", "luz");
      if (p.puerto) {
        luz.title = "apagado";
        b.luz = luz;
      } else {
        luz.classList.add("viva");
        luz.title = "se puede abrir";
      }
      pie.appendChild(luz);
    }

    b.appendChild(marco);
    b.appendChild(pie);
    b.addEventListener("click", function () { ficha(p, verbo); });
    b.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter" || ev.key === " ") {
        ev.preventDefault();
        ficha(p, verbo);
      }
    });
    return b;
  }

  function fila(titulo, items, verbo, contador) {
    var sec = el("section", "fila");

    var rotulo = el("p", "flabel", titulo);
    var s = el("s", null, contador !== undefined ? contador : String(items.length));
    rotulo.appendChild(s);

    var pista = el("div", "pista");
    var cartas = items.map(function (p) {
      var c = carta(p, verbo);
      pista.appendChild(c);
      return c;
    });

    sec.appendChild(rotulo);
    sec.appendChild(pista);
    sec.rotuloContador = s;
    sec.cartas = cartas;
    return sec;
  }

  function filas(cont, grupos, opciones) {
    opciones = opciones || {};
    if (opciones.base) base = opciones.base;
    cont.textContent = "";

    var conLuz = [];

    grupos.forEach(function (g) {
      var items = g.items;
      if (opciones.filtrar) items = items.filter(function (p) { return opciones.filtrar(p, g); });
      if (!items.length) return;
      var sec = fila(g.titulo, items, g.verbo);
      cont.appendChild(sec);
      sec.cartas.forEach(function (c, i) {
        if (c.luz) conLuz.push({puerto: items[i].puerto, luz: c.luz});
      });
    });

    return conLuz;
  }

  return {filas: filas, ficha: ficha, linkSeguro: linkSeguro};
})();
