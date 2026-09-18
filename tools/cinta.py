# -*- coding: utf-8 -*-
"""La cinta del portfolio al pie de cada uno de los sitios de ejemplo.

Es lo único de cada sitio que no pertenece al negocio ficticio: vuelve a la portada, pasa
al sitio siguiente y ofrece pedir uno igual. Antes era un bloque copiado a mano en doce
archivos; ahora se genera desde acá, con el orden de la portada (el array SITIOS de
sitios/index.html), así un sitio nuevo entra en la ronda con solo volver a correrlo.

Correrlo dos veces no cambia nada la segunda.

Uso:  py -3 tools/cinta.py
"""
import io, os, re, sys
from urllib.parse import quote

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTADA = os.path.join(RAIZ, 'sitios', 'index.html')
MAIL = 'nass.ia9000@gmail.com'

INICIO = '<!-- cinta del portfolio: la genera tools/cinta.py, no editar a mano -->'
FIN = '<!-- /cinta del portfolio -->'

CSS = """
  /* Va por debajo de carrito, visor y ventanas de cada sitio (90) y por encima de sus
     barras de navegación (50-60): antes, con 9999, tapaba el botón de pagar. */
  /* Es un div y no un <nav>, y fija top/right/ancho/alto: varios sitios estilan su propio
     nav (fixed, inset 0 0 auto) y la cinta heredaba eso y se estiraba a todo el ancho. */
  .cinta-portfolio{position:fixed;left:16px;bottom:16px;top:auto;right:auto;z-index:80;display:flex;
    width:auto;height:auto;margin:0;padding:0;
    background:rgba(18,18,20,.9);border:1px solid rgba(244,244,242,.18);border-radius:100px;
    backdrop-filter:blur(8px);box-shadow:0 6px 22px rgba(0,0,0,.28);overflow:hidden;
    font:500 14px/1 system-ui,-apple-system,"Segoe UI",sans-serif}
  .cinta-portfolio a{display:inline-flex;align-items:center;gap:7px;padding:12px 15px;margin:0;
    color:#F4F4F2;text-decoration:none;white-space:nowrap;transition:background .2s;
    letter-spacing:normal;text-transform:none;font:inherit}
  .cinta-portfolio a + a{border-left:1px solid rgba(244,244,242,.16)}
  .cinta-portfolio a:hover{background:rgba(244,244,242,.1)}
  .cinta-portfolio a:focus-visible{outline:2px solid #7FA9DC;outline-offset:-3px}
  .cinta-portfolio .cinta-pedir{background:#F4F4F2;color:#121214}
  .cinta-portfolio .cinta-pedir:hover{background:#fff}
  .cinta-portfolio .corto{display:none}
  @media(max-width:520px){
    .cinta-portfolio{left:12px;bottom:12px;font-size:13px}
    .cinta-portfolio a{padding:11px 12px}
    .cinta-portfolio .largo{display:none}
    .cinta-portfolio .corto{display:inline}
  }
  @media print{.cinta-portfolio{display:none}}

  /* Quien pidió menos movimiento en el sistema no ve deslizarse nada. Se acorta en vez de
     sacarse: lo que aparece al hacer scroll igual llega a su estado final. */
  @media (prefers-reduced-motion:reduce){
    html{scroll-behavior:auto!important}
    *,*::before,*::after{animation-duration:.01ms!important;animation-delay:0s!important;
      animation-iteration-count:1!important;transition-duration:.01ms!important;
      transition-delay:0s!important}
  }
"""


def sitios():
    s = io.open(PORTADA, encoding='utf-8').read()
    lista = re.findall(r"slug:'([a-z]+)'[^}]*?nom:'([^']+)'", s)
    if len(lista) < 2:
        raise SystemExit('no encontré el array SITIOS en la portada')
    return [(slug, nom.split(' · ')[0]) for slug, nom in lista]


def bloque(nombre, sig_slug, sig_nombre):
    asunto = quote('Quiero un sitio como ' + nombre)
    return (
        INICIO + '\n'
        '<div class="cinta-portfolio" role="navigation" aria-label="Portfolio">\n'
        '  <a class="cinta-volver" href="/sitios/"><span aria-hidden="true">←</span> '
        '<span class="largo">Ver todos los sitios</span><span class="corto">Sitios</span></a>\n'
        '  <a class="cinta-sig" href="/sitios/%s/" aria-label="Siguiente sitio: %s" title="Siguiente: %s">'
        'Siguiente <span aria-hidden="true">→</span></a>\n'
        '  <a class="cinta-pedir" href="mailto:%s?subject=%s">Quiero uno así</a>\n'
        '</div>\n'
        '<style>%s</style>\n' % (sig_slug, sig_nombre, sig_nombre, MAIL, asunto, CSS)
        + FIN)


def main():
    lista = sitios()
    cambios = 0
    for i, (slug, nombre) in enumerate(lista):
        sig_slug, sig_nombre = lista[(i + 1) % len(lista)]
        ruta = os.path.join(RAIZ, 'sitios', slug, 'index.html')
        with io.open(ruta, encoding='utf-8', newline='') as f:
            s = f.read()
        eol = '\r\n' if '\r\n' in s else '\n'
        nuevo = bloque(nombre, sig_slug, sig_nombre).replace('\n', eol)

        if INICIO in s:
            patron = re.escape(INICIO) + r'.*?' + re.escape(FIN)
        else:
            # la primera vez: la cinta vieja, del <a class="volver-portfolio"> a su </style>
            patron = r'<a class="volver-portfolio".*?</style>'
        s2, n = re.subn(patron, lambda m: nuevo, s, count=1, flags=re.S)
        if n != 1:
            print('  ! %s: no encontré la cinta' % slug)
            continue
        if s2 != s:
            with io.open(ruta, 'w', encoding='utf-8', newline='') as f:
                f.write(s2)
            cambios += 1
        print('  %-13s -> siguiente: %s' % (slug, sig_slug))
    print('%d sitios, %d cambiados' % (len(lista), cambios))


if __name__ == '__main__':
    sys.exit(main())
