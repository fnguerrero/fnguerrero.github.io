# -*- coding: utf-8 -*-
"""Portadas livianas para las tarjetas del taller.

La tarjeta muestra la portada a unos 280 px de ancho (74 px en el celular), pero algunas
capturas son de 1100 px y pesan hasta 180 KB: la solapa de sitios web bajaba casi un
mega para dibujar miniaturas. Esto genera una version de 640x360 en img/min/ para cada
portada de mas de 640 px, la pone como "img" (la tarjeta) y deja la grande en "imgs"
(la galeria de la ficha), que es donde se mira en serio.

Correrlo de nuevo no rompe nada: lo que ya tiene miniatura se regenera igual.

Uso:  py -3 tools/miniaturas.py
"""
import io, json, os, re
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(RAIZ, 'proyectos.json')
ANCHO, ALTO = 640, 360


def sin_version(ruta):
    return re.sub(r'\?.*$', '', ruta)


def miniatura(origen, destino):
    im = Image.open(origen).convert('RGB')
    w, h = im.size
    # Recorte 16:9 desde arriba: en una captura de sitio lo que identifica es la cabecera.
    alto = round(w * ALTO / ANCHO)
    if alto <= h:
        im = im.crop((0, 0, w, alto))
    else:
        ancho = round(h * ANCHO / ALTO)
        x = (w - ancho) // 2
        im = im.crop((x, 0, x + ancho, h))
    im = im.resize((ANCHO, ALTO), Image.LANCZOS)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    im.save(destino, 'JPEG', quality=80, optimize=True, progressive=True)


def main():
    d = json.load(io.open(DATOS, encoding='utf-8'))
    antes = despues = hechas = 0
    for g in d['grupos']:
        for p in g['items']:
            if not p.get('img'):
                continue
            # La portada original es la primera de la galeria si hay galeria.
            grande = sin_version((p.get('imgs') or [p['img']])[0])
            if grande.startswith('img/min/'):
                continue
            ruta = os.path.join(RAIZ, grande)
            if not os.path.isfile(ruta) or Image.open(ruta).size[0] <= ANCHO:
                continue
            chica = 'img/min/' + os.path.basename(grande)
            miniatura(ruta, os.path.join(RAIZ, chica))
            antes += os.path.getsize(ruta)
            despues += os.path.getsize(os.path.join(RAIZ, chica))
            if not p.get('imgs'):
                p['imgs'] = [p['img']]
            p['img'] = chica
            hechas += 1
            print('  %-28s %4d KB -> %3d KB' % (p['nombre'][:28], os.path.getsize(ruta) // 1024,
                                              os.path.getsize(os.path.join(RAIZ, chica)) // 1024))
    json.dump(d, io.open(DATOS, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    if hechas:
        print('%d miniaturas: %d KB -> %d KB (%d%% menos)' % (
            hechas, antes // 1024, despues // 1024, round(100 - 100.0 * despues / antes)))
    else:
        print('nada que achicar')


if __name__ == '__main__':
    main()
