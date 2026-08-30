/* ═══════════════════════════════════════════════════════════════════════
   La franja de arriba: fecha y hora, próximo feriado, dólar y clima.
   La usan las dos páginas. Todo sale de APIs públicas sin clave, y si
   alguna no contesta su chip simplemente no aparece.
   ═══════════════════════════════════════════════════════════════════════ */

(function () {
  "use strict";

  var franja = document.getElementById("franja");
  if (!franja) return;

  function pedir(url) {
    var ctrl = new AbortController();
    setTimeout(function () { ctrl.abort(); }, 6000);
    return fetch(url, {signal: ctrl.signal}).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    });
  }

  // El orden fijo evita que los chips se acomoden según cuál API contesta primero.
  function chip(clave, valor, extra, clase, titulo, orden) {
    var d = document.createElement("div");
    d.className = "dato" + (clase ? " " + clase : "");
    if (titulo) d.title = titulo;
    if (orden) d.style.order = orden;
    var k = document.createElement("span");
    k.className = "k";
    k.textContent = clave;
    var v = document.createElement("span");
    v.className = "v";
    v.textContent = valor;
    d.appendChild(k);
    d.appendChild(v);
    if (extra) {
      var x = document.createElement("span");
      x.className = "x";
      x.textContent = extra;
      d.appendChild(x);
    }
    franja.appendChild(d);
  }

  /* ───────── reloj y feriado ───────── */

  var DIAS = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];
  var MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
               "septiembre", "octubre", "noviembre", "diciembre"];
  var textoFeriado = "", tituloFeriado = "";

  function reloj() {
    var caja = document.getElementById("reloj");
    if (!caja) return;
    var d = new Date();
    caja.textContent = "";

    var k = document.createElement("span");
    k.className = "k";
    k.textContent = DIAS[d.getDay()] + " " + d.getDate() + " " + MESES[d.getMonth()].slice(0, 3);
    var v = document.createElement("span");
    v.className = "v";
    v.textContent = String(d.getHours()).padStart(2, "0") + ":" +
                    String(d.getMinutes()).padStart(2, "0");
    caja.appendChild(k);
    caja.appendChild(v);

    if (textoFeriado) {
      var x = document.createElement("span");
      x.className = "x";
      x.textContent = textoFeriado;
      x.title = tituloFeriado;
      caja.appendChild(x);
    }
  }
  reloj();
  setInterval(reloj, 30000);

  /* ───────── dólar ───────── */

  var pesos = new Intl.NumberFormat("es-AR", {maximumFractionDigits: 0});

  pedir("https://dolarapi.com/v1/dolares").then(function (lista) {
    var nombres = {blue: "blue", oficial: "oficial", bolsa: "MEP"};
    ["blue", "oficial", "bolsa"].forEach(function (casa, i) {
      var d = lista.filter(function (x) { return x.casa === casa; })[0];
      // La compra va al tooltip: si va en el chip, la franja no entra en una sola fila.
      // El primero lleva "derecha": empuja las tres cotizaciones al margen derecho.
      if (d) chip(nombres[casa], "$" + pesos.format(d.venta), null,
                  i === 0 ? "dolar derecha" : "dolar", 
                  "compra " + pesos.format(d.compra) + " · venta " + pesos.format(d.venta),
                  i + 3);
    });
  }).catch(function () {});

  /* ───────── clima ───────── */

  var CIELO = {
    0: "despejado", 1: "casi despejado", 2: "algo nublado", 3: "nublado",
    45: "niebla", 48: "niebla", 51: "llovizna", 53: "llovizna", 55: "llovizna",
    61: "lluvia", 63: "lluvia", 65: "lluvia fuerte", 71: "nieve", 73: "nieve", 75: "nieve",
    80: "chaparrones", 81: "chaparrones", 82: "chaparrones fuertes",
    95: "tormenta", 96: "tormenta", 99: "tormenta"
  };

  pedir("https://api.open-meteo.com/v1/forecast?latitude=-34.61&longitude=-58.38" +
        "&current=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min," +
        "precipitation_probability_max&timezone=America%2FArgentina%2FBuenos_Aires&forecast_days=1")
    .then(function (d) {
      var ahora = Math.round(d.current.temperature_2m);
      var cielo = CIELO[d.current.weather_code] || "";
      var max = Math.round(d.daily.temperature_2m_max[0]);
      var min = Math.round(d.daily.temperature_2m_min[0]);
      var lluvia = d.daily.precipitation_probability_max[0];
      var extra = min + "° / " + max + "°" + (lluvia >= 30 ? " · " + lluvia + "% lluvia" : "");
      chip("Buenos Aires", ahora + "° " + cielo, extra, "clima", null, 2);
    }).catch(function () {});

  /* ───────── próximo feriado ───────── */

  pedir("https://api.argentinadatos.com/v1/feriados/" + new Date().getFullYear())
    .then(function (lista) {
      var hoy = new Date();
      hoy.setHours(0, 0, 0, 0);
      var prox = lista.map(function (f) {
        var p = f.fecha.split("-");
        return {nombre: f.nombre, fecha: new Date(+p[0], +p[1] - 1, +p[2])};
      }).filter(function (f) { return f.fecha >= hoy; })
        .sort(function (a, b) { return a.fecha - b.fecha; })[0];
      if (!prox) return;
      var dias = Math.round((prox.fecha - hoy) / 86400000);
      var cuando = dias === 0 ? "hoy" : dias === 1 ? "mañana" : "en " + dias + " días";
      // Los nombres largos no entran en el chip: van al tooltip.
      textoFeriado = prox.nombre.length > 22 ? "feriado " + cuando : prox.nombre + ", " + cuando;
      tituloFeriado = prox.nombre + ", " + cuando;
      reloj();
    }).catch(function () {});
})();
