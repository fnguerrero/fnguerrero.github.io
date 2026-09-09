# -*- coding: utf-8 -*-
"""Genera sitemap.xml y robots.txt.

Las URLs salen de dos lados: las páginas propias del portfolio (el taller, el apartado y
cada sitio de ejemplo) y los proyectos de proyectos.json que estén publicados en este
mismo dominio. Así, cuando se suma un proyecto al JSON, entra al sitemap solo con volver
a correr esto.
"""
import io, json, os, datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMINIO = 'https://fnguerrero.github.io'
HOY = datetime.date.today().isoformat()


def urls():
    # el taller primero: es la puerta de entrada
    fijas = [(DOMINIO + '/taller/', '1.0'), (DOMINIO + '/sitios/', '0.9')]

    base = os.path.join(RAIZ, 'sitios')
    ejemplos = [(DOMINIO + '/sitios/%s/' % d, '0.7')
                for d in sorted(os.listdir(base))
                if os.path.isfile(os.path.join(base, d, 'index.html'))]

    d = json.load(io.open(os.path.join(RAIZ, 'proyectos.json'), encoding='utf-8'))
    proyectos = []
    for g in d['grupos']:
        for i in g['items']:
            u = i.get('url', '')
            # solo lo publicado en este dominio, y sin repetir lo que ya está arriba
            if u.startswith(DOMINIO) and '/sitios/' not in u:
                proyectos.append((u, '0.6'))

    vistas, salida = set(), []
    for u, p in fijas + ejemplos + sorted(set(proyectos)):
        if u not in vistas:
            vistas.add(u)
            salida.append((u, p))
    return salida


def main():
    lista = urls()
    x = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, p in lista:
        x += ['  <url>', '    <loc>%s</loc>' % u, '    <lastmod>%s</lastmod>' % HOY,
              '    <priority>%s</priority>' % p, '  </url>']
    x.append('</urlset>')
    io.open(os.path.join(RAIZ, 'sitemap.xml'), 'w', encoding='utf-8').write('\n'.join(x) + '\n')

    io.open(os.path.join(RAIZ, 'robots.txt'), 'w', encoding='utf-8').write(
        'User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n' % DOMINIO)

    print('sitemap.xml con %d URLs' % len(lista))
    for u, _ in lista[:4]:
        print('  ', u)
    print('   …')


if __name__ == '__main__':
    main()
