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

  /* Minusculas y sin acentos. Nadie escribe "Déficit" con tilde en un buscador, y sin
     esto "deficit" no encontraba nada. */
  function plano(s) {
    return String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  /* El nombre como pedazo de URL: "Dragon Ball — El Ki de Paozu" -> dragon-ball-el-ki-de-paozu.
     Es la misma regla con la que se nombran las portadas en img/. */
  function slug(nombre) {
    return plano(nombre).replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  }

  // Para compartir desde la home local no sirve un link a localhost: se comparte la
  // pagina publica, que tiene los mismos proyectos.
  var PUBLICA = "https://fnguerrero.github.io/taller/";

  function linkDeFicha(p) {
    var aca = location.protocol === "https:" ? location.origin + location.pathname : PUBLICA;
    return aca + "#" + slug(p.nombre);
  }

  /* "hace 3 dias" a partir de la fecha del ultimo commit.

     Se muestra en la tarjeta porque distingue de un vistazo lo que esta vivo de lo que
     quedo congelado, que mirando una grilla de portadas no se nota. */
  function haceCuanto(iso) {
    if (!iso) return null;
    var cuando = new Date(iso + "T12:00:00");
    if (isNaN(cuando)) return null;
    var dias = Math.floor((Date.now() - cuando) / 86400000);
    if (dias <= 0) return "hoy";
    if (dias === 1) return "ayer";
    if (dias < 30) return "hace " + dias + " días";
    var meses = Math.round(dias / 30.44);
    if (meses < 12) return "hace " + meses + (meses === 1 ? " mes" : " meses");
    var anios = Math.round(dias / 365.25);
    return "hace " + anios + (anios === 1 ? " año" : " años");
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
  var abierta = null;      // slug de la ficha abierta
  var empujada = false;    // si la ficha agrego una entrada al historial
  var precargadas = {};

  // Cerrar la ficha vuelve una entrada en el historial, y el navegador aprovechaba para
  // "restaurar" un scroll viejo: la pagina saltaba a otra seccion. Las entradas de la
  // ficha no cambian de pagina, asi que el scroll se deja quieto.
  if ("scrollRestoration" in history) history.scrollRestoration = "manual";

  function armarDialogo() {
    dlg = document.getElementById("detalle");
    if (dlg) return;

    dlg = document.createElement("dialog");
    dlg.id = "detalle";
    dlg.innerHTML =
      '<div class="ficha">' +
        '<div class="galeria">' +
          '<img class="grande" alt="">' +
          '<button class="paso izq" type="button" title="Anterior" aria-label="Captura anterior">‹</button>' +
          '<button class="paso der" type="button" title="Siguiente" aria-label="Captura siguiente">›</button>' +
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

    // En el celular las flechas quedan chicas: la galeria se pasa deslizando. Solo
    // cuenta un gesto claramente horizontal, para no robarle el scroll vertical a nadie.
    var desde = null;
    gal.addEventListener("pointerdown", function (ev) {
      if (ev.target.closest("button")) return;
      desde = {x: ev.clientX, y: ev.clientY};
    });
    gal.addEventListener("pointerup", function (ev) {
      if (!desde || fotos.length < 2) { desde = null; return; }
      var dx = ev.clientX - desde.x, dy = ev.clientY - desde.y;
      desde = null;
      if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy) * 1.5) {
        mostrar(actual + (dx < 0 ? 1 : -1));
      }
    });
    gal.addEventListener("pointercancel", function () { desde = null; });

    /* La ficha vive en el historial: tiene link propio (#slug) y el boton atras del
       celular la cierra en vez de sacarte de la pagina. */
    dlg.addEventListener("close", function () {
      var eraLaDelLink = location.hash === "#" + abierta;
      abierta = null;
      if (!eraLaDelLink) { empujada = false; return; }
      if (empujada) {
        empujada = false;
        history.back();
      } else {
        history.replaceState(null, "", location.pathname + location.search);
      }
    });
    window.addEventListener("popstate", function () {
      var h = decodeURIComponent(location.hash.slice(1));
      if (dlg.open && h !== abierta) {
        empujada = false;
        dlg.close();
      } else if (!dlg.open && indice[h]) {
        ficha(indice[h].p, indice[h].verbo, true);
      }
    });
  }

  function precargar(i) {
    var src = fotos[(i + fotos.length) % fotos.length];
    if (!src || precargadas[src]) return;
    precargadas[src] = new Image();
    precargadas[src].src = src;
  }

  function mostrar(i) {
    if (!fotos.length) return;
    actual = (i + fotos.length) % fotos.length;
    grande.src = fotos[actual];
    Array.prototype.forEach.call(puntos.children, function (b, n) {
      b.classList.toggle("activo", n === actual);
      if (n === actual) b.setAttribute("aria-current", "true");
      else b.removeAttribute("aria-current");
    });
    // Las vecinas se piden antes de que las pidan: en el celular, pasar a una captura
    // que todavia no bajo dejaba el marco en blanco un momento.
    if (fotos.length > 1) { precargar(actual + 1); precargar(actual - 1); }
  }

  /* Compartir: en el telefono, la hoja de compartir del sistema (WhatsApp y compania);
     en la compu, copiar el link, que es lo que uno quiere para pegarlo en otro lado. */
  function compartir(p, boton) {
    var url = linkDeFicha(p);
    var tactil = window.matchMedia && matchMedia("(pointer:coarse)").matches;
    if (tactil && navigator.share) {
      navigator.share({title: p.nombre, text: p.tag || p.nombre, url: url}).catch(function () {});
      return;
    }
    function avisar(texto) {
      boton.textContent = texto;
      clearTimeout(boton.t);
      boton.t = setTimeout(function () { boton.textContent = "Compartir"; }, 1800);
    }
    function aMano() {
      var t = document.createElement("textarea");
      t.value = url;
      t.style.cssText = "position:fixed;opacity:0";
      dlg.appendChild(t);
      t.select();
      var ok = false;
      try { ok = document.execCommand("copy"); } catch (e) {}
      t.remove();
      if (ok) { avisar("Link copiado"); return; }
      // Ultimo recurso (navegadores que no dejan tocar el portapapeles): el link a la
      // vista, ya seleccionado, para copiarlo a mano.
      window.prompt("Copiá el link:", url);
    }
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(url).then(function () { avisar("Link copiado"); }, aMano);
    } else {
      aMano();
    }
  }

  function ficha(p, verbo, desdeHistorial) {
    armarDialogo();

    fotos = imagenes(p);
    var varias = fotos.length > 1;
    gal.style.display = fotos.length ? "" : "none";
    izq.style.display = der.style.display = varias ? "" : "none";

    puntos.textContent = "";
    if (varias) {
      fotos.forEach(function (_, n) {
        var b = document.createElement("button");
        b.type = "button";
        b.setAttribute("aria-label", "Captura " + (n + 1) + " de " + fotos.length);
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
    // Lo privado no tiene pagina publica a la que llevar el link.
    if (!p.privado) {
      var comp = el("button", "btn suave", "Compartir");
      comp.type = "button";
      comp.addEventListener("click", function () { compartir(p, comp); });
      acc.appendChild(comp);
    }
    var x = el("button", "cerrar", "cerrar");
    x.addEventListener("click", function () { dlg.close(); });
    acc.appendChild(x);

    var s = slug(p.nombre);
    if (!desdeHistorial && !p.privado && location.hash !== "#" + s) {
      history.pushState({ficha: s}, "", "#" + s);
      empujada = true;
    }
    abierta = s;
    if (!dlg.open) dlg.showModal();
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
      // "img" es la portada de la tarjeta e "imgs" la galeria de la ficha. Cuando estan
      // las dos, la tarjeta puede ir con una version mas liviana que la de la ficha.
      img.src = p.img && p.imgs ? imagenes({img: p.img})[0] : fotos[0];
      img.alt = "Portada de " + p.nombre;
      img.loading = "lazy";
      // Las portadas son todas 16:9. Declararlo evita que el navegador tenga que esperar
      // a la imagen para saber cuánto alto reservar, y que la grilla salte al cargar.
      img.width = 1600;
      img.height = 900;
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

    var cuando = haceCuanto(p.tocado);
    if (cuando) {
      var t = el("time", "tocado", cuando);
      t.dateTime = p.tocado;
      t.title = "Último cambio: " + p.tocado;
      pie.appendChild(t);
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

  // Las secciones dibujadas, para que el buscador pueda esconder y volver a mostrar sin
  // repintar nada.
  var secciones = [];
  var indice = {};         // slug -> {p, verbo}, para abrir fichas desde el link
  var vacio = null, inputBuscar = null;

  /* Todo el texto por el que se puede encontrar un proyecto. */
  function buscable(p) {
    return plano([p.nombre, p.tag, p.que].concat(p.chips || []).join(" "));
  }

  function filtrar(texto) {
    var q = plano((texto || "").trim());
    var total = 0;
    secciones.forEach(function (s) {
      var visibles = 0;
      s.cartas.forEach(function (carta, i) {
        var entra = !q || buscable(s.items[i]).indexOf(q) !== -1;
        carta.style.display = entra ? "" : "none";
        if (entra) visibles++;
      });
      s.sec.style.display = visibles ? "" : "none";
      s.contador.textContent = visibles;
      total += visibles;
    });
    // Sin esto, una busqueda sin resultados dejaba la pagina en blanco, como rota.
    if (vacio) {
      vacio.hidden = !(q && total === 0);
      vacio.firstChild.textContent = "Nada con «" + (texto || "").trim() + "». ";
    }
    return total;
  }

  function limpiarBusqueda() {
    if (inputBuscar) {
      inputBuscar.value = "";
      inputBuscar.dispatchEvent(new Event("input"));
      inputBuscar.focus();
    } else {
      filtrar("");
    }
  }

  /* El buscador. Se arma solo, para no repetir el markup en las dos paginas. */
  function armarBuscador(solapas) {
    var caja = el("div", "buscar");
    var input = document.createElement("input");
    input.type = "search";
    input.placeholder = "Buscar…";
    input.setAttribute("aria-label", "Buscar entre los proyectos");
    var cuenta = el("span", "cuenta-busqueda", "");
    inputBuscar = input;

    input.addEventListener("input", function () {
      var n = filtrar(input.value);
      if (solapas) solapas.suspender(input.value.trim());
      cuenta.textContent = input.value.trim()
        ? (n === 0 ? "nada" : n === 1 ? "1 resultado" : n + " resultados")
        : "";
    });
    input.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape") {
        input.value = ""; filtrar(""); cuenta.textContent = "";
        if (solapas) solapas.suspender(false);
      }
    });

    // Barra inclinada para buscar, como en cualquier lado. Enter no hace falta: filtra
    // mientras se escribe.
    document.addEventListener("keydown", function (ev) {
      var enUnCampo = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
      if (ev.key === "/" && !enUnCampo) { ev.preventDefault(); input.focus(); }
    });

    caja.appendChild(input);
    caja.appendChild(cuenta);
    return caja;
  }

  /* Las solapas del telefono. Ocultan con una clase y no tocan style.display, que es de
     quien busca: asi los dos pueden esconder secciones sin pisarse. Mientras hay algo
     escrito en el buscador las solapas se apagan y mandan los resultados. */
  function armarSolapas(cont, secciones) {
    if (secciones.length < 2) return null;

    var barra = el("nav", "solapas");
    barra.setAttribute("role", "tablist");
    barra.setAttribute("aria-label", "Grupos de proyectos");

    var elegida = 0;
    try {
      var guardada = secciones.map(function (s) { return s.titulo; })
                              .indexOf(localStorage.getItem("taller.solapa"));
      if (guardada > -1) elegida = guardada;
    } catch (e) {}

    var botones = secciones.map(function (s, i) {
      var b = document.createElement("button");
      b.type = "button";
      b.setAttribute("role", "tab");
      b.id = "solapa-" + slug(s.titulo);
      s.sec.id = "grupo-" + slug(s.titulo);
      b.setAttribute("aria-controls", s.sec.id);
      b.appendChild(document.createTextNode(s.titulo));
      var n = el("s", null, String(s.cartas.length));
      b.appendChild(n);
      b.addEventListener("click", function () { activar(i); });
      barra.appendChild(b);
      return b;
    });

    // Como cualquier lista de pestañas: Tab entra a la elegida y las flechas pasan de una
    // a otra (Inicio y Fin van a la primera y a la última). Solo la elegida es tabulable,
    // así Tab no obliga a recorrer las cuatro para llegar a las tarjetas.
    barra.addEventListener("keydown", function (ev) {
      var n = botones.length, a = elegida;
      if (ev.key === "ArrowRight") a = (elegida + 1) % n;
      else if (ev.key === "ArrowLeft") a = (elegida - 1 + n) % n;
      else if (ev.key === "Home") a = 0;
      else if (ev.key === "End") a = n - 1;
      else return;
      ev.preventDefault();
      activar(a);
      botones[a].focus();
    });

    function activar(i) {
      elegida = i;
      secciones.forEach(function (s, k) {
        s.sec.classList.toggle("sin-solapa", k !== i);
        botones[k].setAttribute("aria-selected", k === i ? "true" : "false");
        botones[k].tabIndex = k === i ? 0 : -1;
      });
      try { localStorage.setItem("taller.solapa", secciones[i].titulo); } catch (e) {}
      botones[i].scrollIntoView({block: "nearest", inline: "nearest"});
    }

    activar(elegida);
    return {barra: barra, suspender: function (buscando) {
      cont.classList.toggle("buscando", !!buscando);
    }};
  }

  function filas(cont, grupos, opciones) {
    opciones = opciones || {};
    if (opciones.base) base = opciones.base;
    cont.textContent = "";
    secciones = [];
    indice = {};

    var conLuz = [];

    grupos.forEach(function (g) {
      var items = g.items;
      if (opciones.filtrar) items = items.filter(function (p) { return opciones.filtrar(p, g); });
      if (!items.length) return;
      items.forEach(function (p) { indice[slug(p.nombre)] = {p: p, verbo: g.verbo}; });
      var sec = fila(g.titulo, items, g.verbo);
      cont.appendChild(sec);
      secciones.push({sec: sec, items: items, cartas: sec.cartas,
                      contador: sec.rotuloContador, titulo: g.titulo});
      sec.cartas.forEach(function (c, i) {
        if (c.luz) conLuz.push({puerto: items[i].puerto, luz: c.luz});
      });
    });

    // Con pocas tarjetas se encuentra todo con el ojo; el buscador recien suma cuando la
    // lista no entra de un vistazo.
    var cuantos = secciones.reduce(function (n, s) { return n + s.cartas.length; }, 0);

    var solapas = armarSolapas(cont, secciones);
    if (solapas) cont.insertBefore(solapas.barra, cont.firstChild);
    if (cuantos >= 10) cont.insertBefore(armarBuscador(solapas), cont.firstChild);

    vacio = el("p", "aviso vacio");
    vacio.appendChild(document.createTextNode(""));
    var limpiar = el("button", "btn suave", "Limpiar búsqueda");
    limpiar.type = "button";
    limpiar.addEventListener("click", limpiarBusqueda);
    vacio.appendChild(limpiar);
    vacio.hidden = true;
    cont.appendChild(vacio);

    // Entrar por un link a una ficha (/taller/#nimbo). Primero se deja la pagina sin el
    // hash y despues se vuelve a poner desde la ficha: asi atras cierra la ficha y no
    // saca de la pagina, igual que cuando se abre con un clic.
    var h = decodeURIComponent(location.hash.slice(1));
    if (indice[h]) {
      history.replaceState(null, "", location.pathname + location.search);
      ficha(indice[h].p, indice[h].verbo);
    }

    return conLuz;
  }

  return {filas: filas, ficha: ficha, filtrar: filtrar, linkSeguro: linkSeguro, slug: slug};
})();
