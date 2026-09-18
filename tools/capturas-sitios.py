# -*- coding: utf-8 -*-
"""Versiones de 640 px de las capturas de los sitios, para la portada de /sitios/.

La portada muestra cada captura a unos 590 px de ancho en escritorio y a todo el ancho en
el celular. Las originales son de 1100 px y pesan hasta 180 KB: con doce, abrir la portada
bajaba casi un mega de imagen. Con estas, el navegador elige solo (srcset) la de 640 donde
alcanza y la grande donde la pantalla la aprovecha.

Mantienen la proporción de la original (sin recorte): la portada las encuadra desde arriba
igual que a la grande, así no cambia el encuadre según qué versión se haya elegido.

Uso:  py -3 tools/capturas-sitios.py
"""
import glob, os
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANCHO = 640


def main():
    destino = os.path.join(RAIZ, 'img', 'sitios-640')
    os.makedirs(destino, exist_ok=True)
    antes = despues = 0
    for f in sorted(glob.glob(os.path.join(RAIZ, 'img', 'sitio-*.jpg'))):
        im = Image.open(f).convert('RGB')
        w, h = im.size
        chica = im.resize((ANCHO, round(h * ANCHO / w)), Image.LANCZOS)
        salida = os.path.join(destino, os.path.basename(f))
        chica.save(salida, 'JPEG', quality=80, optimize=True, progressive=True)
        antes += os.path.getsize(f)
        despues += os.path.getsize(salida)
        print('  %-26s %dx%d %4d KB -> %dx%d %3d KB' % (
            os.path.basename(f), w, h, os.path.getsize(f) // 1024,
            chica.size[0], chica.size[1], os.path.getsize(salida) // 1024))
    print('total: %d KB -> %d KB' % (antes // 1024, despues // 1024))


if __name__ == '__main__':
    main()
