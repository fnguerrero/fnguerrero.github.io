# -*- coding: utf-8 -*-
"""Pone a cada imagen de proyectos.json un ?v= con el hash de su contenido.

Antes cada ?v= era un timestamp puesto a mano, y las portadas nuevas entraban sin
ninguno: una captura reemplazada podia seguir viendose vieja por la cache del navegador
o de WhatsApp. Con el hash, la version cambia exactamente cuando cambia el archivo, y lo
que no cambio sigue aprovechando la cache.

Correrlo dos veces seguidas no cambia nada (la segunda dice "0 cambios").

Uso:  py -3 tools/versionar.py
"""
import hashlib, io, json, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(RAIZ, 'proyectos.json')


def huella(ruta):
    return hashlib.md5(open(ruta, 'rb').read()).hexdigest()[:8]


def versionar(src, faltan):
    if re.match(r'^https?:', src):
        return src
    limpio = re.sub(r'\?.*$', '', src)
    ruta = os.path.join(RAIZ, limpio)
    if not os.path.isfile(ruta):
        faltan.append(limpio)
        return src
    return '%s?v=%s' % (limpio, huella(ruta))


def main():
    texto = io.open(DATOS, encoding='utf-8').read()
    d = json.loads(texto)
    cambios, total, faltan = 0, 0, []
    for g in d['grupos']:
        for p in g['items']:
            if p.get('img'):
                total += 1
                nuevo = versionar(p['img'], faltan)
                cambios += nuevo != p['img']
                p['img'] = nuevo
            if p.get('imgs'):
                nuevas = [versionar(i, faltan) for i in p['imgs']]
                total += len(nuevas)
                cambios += sum(a != b for a, b in zip(nuevas, p['imgs']))
                p['imgs'] = nuevas
    if cambios:
        json.dump(d, io.open(DATOS, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('%d imagenes, %d cambios' % (total, cambios))
    for f in faltan:
        print('  ! no existe:', f)
    return 1 if faltan else 0


if __name__ == '__main__':
    sys.exit(main())
