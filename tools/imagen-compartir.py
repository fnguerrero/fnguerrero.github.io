# -*- coding: utf-8 -*-
"""La imagen que aparece cuando se pega el link del taller en WhatsApp o en redes.

Antes era el icono cuadrado de 512 px, que con tarjeta grande sale recortado y no dice
nada de lo que hay adentro. Esta es de 1200x630 (la medida que piden WhatsApp, Facebook
y X) y esta armada con portadas reales: se ve de un vistazo que hay apps, juegos y sitios.

Uso:  py -3 tools/imagen-compartir.py
"""
import io, json, os, re
from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, 'img', 'taller-compartir.jpg')
W, H = 1200, 630
FONDO = (11, 15, 20)
FUENTES = r'C:\Windows\Fonts'

# Una mezcla de los tres grupos, alternada para que no queden dos del mismo tipo juntas.
ELEGIDOS = ['NIMBO', 'Déficit', 'Bodega Alto Verde', 'La Previa',
            'Multimarket', 'Gráfica Sur', 'SIMA-7', 'Paid',
            'Norte Propiedades', 'Dragon Ball — El Ki de Paozu', 'Álbum Panini 2026', 'El Fogón']


def portada(p):
    src = (p.get('imgs') or [p['img']])[0]
    return os.path.join(RAIZ, re.sub(r'\?.*$', '', src))


def cubrir(im, w, h):
    iw, ih = im.size
    escala = max(w / iw, h / ih)
    im = im.resize((round(iw * escala), round(ih * escala)), Image.LANCZOS)
    x = (im.size[0] - w) // 2
    return im.crop((x, 0, x + w, h))


def main():
    d = json.load(io.open(os.path.join(RAIZ, 'proyectos.json'), encoding='utf-8'))
    todos = {p['nombre']: p for g in d['grupos'] for p in g['items']}
    faltan = [n for n in ELEGIDOS if n not in todos]
    if faltan:
        raise SystemExit('no estan en proyectos.json: %s' % faltan)

    lienzo = Image.new('RGB', (W, H), FONDO)
    cols, filas, gap, margen = 4, 3, 14, 26
    tw = (W - 2 * margen - gap * (cols - 1)) // cols
    th = round(tw * 9 / 16)
    # la grilla empieza un poco por encima del borde: la franja del titulo tapa la fila de abajo
    y0 = -th // 3
    for i, nombre in enumerate(ELEGIDOS):
        c, f = i % cols, i // cols
        im = cubrir(Image.open(portada(todos[nombre])).convert('RGB'), tw, th)
        mascara = Image.new('L', (tw, th), 0)
        ImageDraw.Draw(mascara).rounded_rectangle((0, 0, tw - 1, th - 1), 10, fill=255)
        lienzo.paste(im, (margen + c * (tw + gap), y0 + f * (th + gap)), mascara)

    # Degradado de abajo hacia arriba para que el titulo se lea sobre las portadas.
    velo = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dv = ImageDraw.Draw(velo)
    desde = 300
    for y in range(desde, H):
        a = min(255, int(255 * ((y - desde) / (H - desde)) ** 0.7 * 1.08))
        dv.line([(0, y), (W, y)], fill=FONDO + (a,))
    lienzo = Image.alpha_composite(lienzo.convert('RGBA'), velo).convert('RGB')

    dr = ImageDraw.Draw(lienzo)
    titulo = ImageFont.truetype(os.path.join(FUENTES, 'segoeuib.ttf'), 76)
    bajada = ImageFont.truetype(os.path.join(FUENTES, 'segoeui.ttf'), 32)
    dr.text((margen + 4, H - 170), 'El taller de Nico', font=titulo, fill=(236, 242, 247))
    dr.text((margen + 6, H - 76), 'Apps, juegos y sitios web que se pueden probar ahora',
            font=bajada, fill=(150, 165, 178))
    # una raya del color de acento del tema neon, para que no sea solo texto gris
    dr.rectangle((margen + 6, H - 186, margen + 86, H - 180), fill=(0, 229, 160))

    lienzo.save(DESTINO, 'JPEG', quality=86, optimize=True, progressive=True)
    print('listo:', DESTINO, lienzo.size, os.path.getsize(DESTINO) // 1024, 'KB')


if __name__ == '__main__':
    main()
