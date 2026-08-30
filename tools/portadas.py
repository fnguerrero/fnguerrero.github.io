# -*- coding: utf-8 -*-
"""Arma las portadas del taller y las anota en proyectos.json.

- Los proyectos publicados: se recorta a 16:9 la captura que dejo Chrome (raw-*.png).
- Los que no tienen URL: se dibuja una portada con el color y la sigla del proyecto.

Correr con: py -3 tools/portadas.py
Las capturas se sacan antes, con:
  chrome --headless=new --window-size=1280,800 --screenshot=img\raw-<slug>.png <url>
"""
import collections
import io
import json
import os
import re

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(AQUI, ".."))
IMG = os.path.join(BASE, "img")
PROPIAS = os.path.join(BASE, "capturas-tuyas")

ANCHO, ALTO = 640, 360

# Portadas dibujadas a mano, que el script no debe pisar.
# Los que se dibujan en vez de fotografiarse. Figumatch tiene su propio script
# (ilustrar-figumatch.py); el resto sale de tools/ilustrar.py, que dibuja la pantalla
# que cada uno declara ahi. Ver el comentario de ese archivo para el porque.
A_MANO = {"Figumatch"}
FUENTE_NEGRITA = r"C:\Windows\Fonts\segoeuib.ttf"
FUENTE_NORMAL = r"C:\Windows\Fonts\segoeui.ttf"
FUENTE_MONO = r"C:\Windows\Fonts\consola.ttf"


def slug(nombre):
    """Nombre de archivo a partir del nombre del proyecto."""
    s = nombre.lower()
    for a, b in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n"),
                 ("—", "-"), ("/", "-")]:
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def borde_de_fondo(im):
    """Color de fondo de la captura: el mas repetido en el marco de afuera."""
    ancho, alto = im.size
    muestras = []
    for x in range(0, ancho, max(1, ancho // 60)):
        muestras.append(im.getpixel((x, 0)))
        muestras.append(im.getpixel((x, alto - 1)))
    for y in range(0, alto, max(1, alto // 60)):
        muestras.append(im.getpixel((0, y)))
        muestras.append(im.getpixel((ancho - 1, y)))
    return collections.Counter(muestras).most_common(1)[0][0]


def recortar_contenido(im, tolerancia=26):
    """Saca el vacio de alrededor.

    Muchas pantallas dejan la mitad de la captura en blanco y el contenido
    queda diminuto en la tarjeta. Se busca hasta donde llega lo que se ve y
    se recorta ahi, con un margen, manteniendo el 16:9.
    """
    fondo = borde_de_fondo(im)
    difs = ImageChops.difference(im, Image.new("RGB", im.size, fondo))
    caja = difs.convert("L").point(lambda v: 255 if v > tolerancia else 0).getbbox()
    if not caja:
        return im

    izq, arr, der, aba = caja
    ancho, alto = im.size
    # Si el contenido ya ocupa casi todo, no se toca.
    if (der - izq) * (aba - arr) > ancho * alto * 0.82:
        return im

    margen_x = int((der - izq) * 0.05)
    margen_y = int((aba - arr) * 0.07)
    izq = max(0, izq - margen_x)
    der = min(ancho, der + margen_x)
    arr = max(0, arr - margen_y)
    aba = min(alto, aba + margen_y)

    # No agrandar mas de 1.8x, ni a lo ancho ni a lo alto: de ahi para arriba
    # se ve pixelado, y un recorte muy chato termina mostrando una franja sin
    # sentido en vez de la pantalla.
    minimo_x = ancho / 1.8
    if der - izq < minimo_x:
        centro = (izq + der) / 2
        izq = int(max(0, min(centro - minimo_x / 2, ancho - minimo_x)))
        der = int(izq + minimo_x)

    minimo_y = alto / 1.8
    if aba - arr < minimo_y:
        centro = (arr + aba) / 2
        arr = int(max(0, min(centro - minimo_y / 2, alto - minimo_y)))
        aba = int(arr + minimo_y)

    return im.crop((izq, arr, der, aba))


def centro_del_contenido(im):
    """Donde esta el peso de lo que se ve, para centrar el recorte ahi."""
    fondo = borde_de_fondo(im)
    difs = ImageChops.difference(im, Image.new("RGB", im.size, fondo))
    mascara = difs.convert("L").point(lambda v: 255 if v > 26 else 0)
    caja = mascara.getbbox()
    if not caja:
        return im.size[0] / 2, im.size[1] / 2
    return (caja[0] + caja[2]) / 2, (caja[1] + caja[3]) / 2


def de_captura(origen, destino):
    """Recorta la captura a 16:9 y la deja en 640x360.

    El recorte se centra en el contenido y no en el medio de la imagen: si no,
    una pantalla con la barra arriba y el cuerpo abajo queda descentrada.
    """
    im = Image.open(origen).convert("RGB")
    im = recortar_contenido(im)

    cx, cy = centro_del_contenido(im)
    objetivo = ANCHO / ALTO
    ancho, alto = im.size

    if ancho / alto > objetivo:                      # sobra a los costados
        nuevo = int(alto * objetivo)
        izq = int(max(0, min(cx - nuevo / 2, ancho - nuevo)))
        im = im.crop((izq, 0, izq + nuevo, alto))
    else:                                            # sobra arriba y abajo
        nuevo = int(ancho / objetivo)
        arr = int(max(0, min(cy - nuevo / 2, alto - nuevo)))
        im = im.crop((0, arr, ancho, arr + nuevo))

    im = im.resize((ANCHO, ALTO), Image.LANCZOS)
    im.save(destino, "JPEG", quality=84, optimize=True, progressive=True)
    return os.path.getsize(destino)


def mezcla(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def hex_a_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def generada(proyecto, destino):
    """Portada dibujada, para lo que no tiene pantalla web que capturar.

    En vez de la sigla sola, se dibuja una ventanita con barra de titulo y
    contenido insinuado, en el color del proyecto. Las que son backend llevan
    un bloque de codigo en lugar de la ventana.
    """
    color = hex_a_rgb(proyecto["color"])
    oscuro = mezcla(color, (10, 12, 14), 0.78)
    claro = mezcla(color, (255, 255, 255), 0.06)

    im = Image.new("RGB", (ANCHO, ALTO))
    d = ImageDraw.Draw(im)
    for y in range(ALTO):
        d.line([(0, y), (ANCHO, y)], fill=mezcla(claro, oscuro, y / (ALTO - 1)))

    es_api = "API" in proyecto["nombre"] or proyecto.get("tag") == "backend"
    vidrio = mezcla(color, (255, 255, 255), 0.90)
    tinta = mezcla(color, (12, 14, 16), 0.55)

    # La ventana, apoyada en el centro.
    vx, vy, vw, vh = 92, 74, ANCHO - 184, ALTO - 176
    sombra = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle([vx + 5, vy + 9, vx + vw + 5, vy + vh + 9],
                                             radius=12, fill=(0, 0, 0, 70))
    im.paste(Image.alpha_composite(im.convert("RGBA"), sombra.filter(
        ImageFilter.GaussianBlur(9))).convert("RGB"), (0, 0))

    d = ImageDraw.Draw(im)
    d.rounded_rectangle([vx, vy, vx + vw, vy + vh], radius=11, fill=vidrio)
    d.rounded_rectangle([vx, vy, vx + vw, vy + 26], radius=11, fill=mezcla(vidrio, tinta, 0.10))
    d.rectangle([vx, vy + 18, vx + vw, vy + 26], fill=mezcla(vidrio, tinta, 0.10))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([vx + 13 + i * 15, vy + 9, vx + 21 + i * 15, vy + 17], fill=c)

    if es_api:
        # Un bloque de codigo: es lo que se ve cuando se le pega a un backend.
        f = ImageFont.truetype(FUENTE_MONO, 15)
        lineas = ["{", '  "estado": "ok",', '  "version": "1.0"', "}"]
        for i, linea in enumerate(lineas):
            d.text((vx + 22, vy + 46 + i * 24), linea, font=f,
                   fill=mezcla(tinta, color, 0.45 if i in (1, 2) else 0.0))
    else:
        # Barra lateral y renglones: la silueta de cualquier app.
        d.rounded_rectangle([vx + 12, vy + 38, vx + 74, vy + vh - 12], radius=7,
                            fill=mezcla(vidrio, tinta, 0.09))
        for i in range(4):
            d.rounded_rectangle([vx + 20, vy + 50 + i * 22, vx + 66, vy + 58 + i * 22],
                                radius=3, fill=mezcla(vidrio, tinta, 0.22))
        anchos = [0.92, 0.66, 0.80, 0.48]
        for i, a in enumerate(anchos):
            largo = int((vw - 108) * a)
            relleno = color if i == 0 else mezcla(vidrio, tinta, 0.16)
            d.rounded_rectangle([vx + 88, vy + 46 + i * 30, vx + 88 + largo, vy + 62 + i * 30],
                                radius=5, fill=relleno)

    # Nombre y bajada, abajo a la izquierda.
    f_nombre = ImageFont.truetype(FUENTE_NEGRITA, 36)
    f_tag = ImageFont.truetype(FUENTE_NORMAL, 19)
    nombre = proyecto["nombre"]
    while d.textlength(nombre, font=f_nombre) > ANCHO - 72 and f_nombre.size > 22:
        f_nombre = ImageFont.truetype(FUENTE_NEGRITA, f_nombre.size - 2)
    d.text((36, ALTO - 84), nombre, font=f_nombre, fill=(255, 255, 255))
    if proyecto.get("tag"):
        d.text((38, ALTO - 40), proyecto["tag"], font=f_tag, fill=(235, 238, 242))

    im.save(destino, "JPEG", quality=88, optimize=True, progressive=True)
    return os.path.getsize(destino)


def sobre_fondo(origen, proyecto, destino):
    """Lleva una captura propia a 640x360 llenando todo el recuadro.

    Se agranda hasta cubrir y se recorta lo que sobra, centrando en donde esta
    el contenido para perder lo menos posible. Si la proporcion es muy distinta
    a 16:9 y el recorte se comeria mas de un tercio, se deja un marco del color
    del proyecto en vez de mutilar la pantalla.
    """
    foto = Image.open(origen).convert("RGB")
    objetivo = ANCHO / ALTO
    proporcion = foto.width / foto.height
    perdida = max(objetivo / proporcion, proporcion / objetivo)

    if perdida <= 1.5:
        # Llena el recuadro: se agranda hasta cubrir y se recorta el sobrante.
        escala = max(ANCHO / foto.width, ALTO / foto.height)
        foto = foto.resize((max(ANCHO, int(foto.width * escala)),
                            max(ALTO, int(foto.height * escala))), Image.LANCZOS)
        cx, cy = centro_del_contenido(foto)
        izq = int(max(0, min(cx - ANCHO / 2, foto.width - ANCHO)))
        arr = int(max(0, min(cy - ALTO / 2, foto.height - ALTO)))
        im = foto.crop((izq, arr, izq + ANCHO, arr + ALTO))
        im.save(destino, "JPEG", quality=86, optimize=True, progressive=True)
        return os.path.getsize(destino)

    # Demasiado angosta o alta: entra entera sobre el color del proyecto.
    color = hex_a_rgb(proyecto["color"])
    oscuro = mezcla(color, (10, 12, 14), 0.74)
    claro = mezcla(color, (255, 255, 255), 0.06)
    im = Image.new("RGB", (ANCHO, ALTO))
    d = ImageDraw.Draw(im)
    for y in range(ALTO):
        d.line([(0, y), (ANCHO, y)], fill=mezcla(claro, oscuro, y / (ALTO - 1)))

    escala = min(ALTO * 0.94 / foto.height, ANCHO * 0.96 / foto.width)
    foto = foto.resize((max(1, int(foto.width * escala)),
                        max(1, int(foto.height * escala))), Image.LANCZOS)
    x = (ANCHO - foto.width) // 2
    y = (ALTO - foto.height) // 2
    sombra = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rectangle([x + 5, y + 9, x + foto.width + 5, y + foto.height + 9],
                                     fill=(0, 0, 0, 95))
    im.paste(Image.alpha_composite(im.convert("RGBA"),
             sombra.filter(ImageFilter.GaussianBlur(11))).convert("RGB"), (0, 0))
    im.paste(foto, (x, y))
    im.save(destino, "JPEG", quality=88, optimize=True, progressive=True)
    return os.path.getsize(destino)


def con_version(ruta_relativa):
    """Le agrega ?v=<fecha del archivo> para que el navegador no sirva la vieja."""
    completa = os.path.join(BASE, ruta_relativa.replace("/", os.sep))
    if not os.path.exists(completa):
        return ruta_relativa
    return "%s?v=%d" % (ruta_relativa, int(os.path.getmtime(completa)))


def main():
    # Las dos listas: la publica y la que se ve solo en la home local.
    for archivo in ("proyectos.json", "privados.json"):
        ruta = os.path.join(BASE, archivo)
        if os.path.exists(ruta):
            print("== " + archivo)
            una_lista(ruta)
    escribir_privados_js()


def una_lista(ruta_json):
    # Adentro de la funcion y no arriba: ilustrar.py importa este modulo, asi que a nivel
    # de archivo se morderian la cola.
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import ilustrar

    datos = json.load(io.open(ruta_json, encoding="utf-8"),
                      object_pairs_hook=collections.OrderedDict)

    for grupo in datos["grupos"]:
        for p in grupo["items"]:
            # Las que se dibujan desde tools/ilustrar.py se rehacen en cada corrida:
            # su fuente es el codigo, no un archivo suelto que se pueda perder.
            if ilustrar.hay_para(p["nombre"]):
                destino = os.path.join(IMG, slug(p["nombre"]) + ".jpg")
                peso = ilustrar.dibujar(p, destino) / 1024
                print("%-28s %-12s %6.1f KB" % (p["nombre"], "dibujada", peso))
                p["img"] = con_version("img/" + slug(p["nombre"]) + ".jpg")
                p.pop("imgs", None)
                continue

            # Las portadas dibujadas por un script propio no se tocan.
            if p["nombre"] in A_MANO:
                ruta = os.path.join(IMG, slug(p["nombre"]) + ".jpg")
                peso = os.path.getsize(ruta) / 1024 if os.path.exists(ruta) else 0
                print("%-28s %-12s %6.1f KB" % (p["nombre"], "ilustrada", peso))
                continue

            nombre_archivo = slug(p["nombre"]) + ".jpg"
            destino = os.path.join(IMG, nombre_archivo)

            # Las capturas se llaman por el repo, que no siempre coincide con el nombre.
            # Puede haber varias: raw-<repo>-1.png, -2, -3 (galeria de la ficha).
            # Se buscan por el nombre del repo y, si no, por el del proyecto: las
            # apps que no se publican no tienen repo pero igual se capturan local.
            claves = []
            if p.get("repo"):
                claves.append(p["repo"].rstrip("/").split("/")[-1])
            if slug(p["nombre"]) not in claves:
                claves.append(slug(p["nombre"]))

            # Lo que deja Nico en capturas-tuyas/ manda sobre el resto.
            propias = []
            for clave in claves:
                for ext in (".png", ".jpg", ".jpeg"):
                    uno = os.path.join(PROPIAS, clave + ext)
                    if os.path.exists(uno) and uno not in propias:
                        propias.append(uno)
                    n = 2
                    while os.path.exists(os.path.join(PROPIAS, "%s-%d%s" % (clave, n, ext))):
                        propias.append(os.path.join(PROPIAS, "%s-%d%s" % (clave, n, ext)))
                        n += 1
                if propias:
                    break

            if propias:
                salidas, peso = [], 0
                for i, foto in enumerate(propias):
                    nombre = slug(p["nombre"]) + ("" if i == 0 else "-%d" % (i + 1)) + ".jpg"
                    peso += sobre_fondo(foto, p, os.path.join(IMG, nombre))
                    salidas.append(con_version("img/" + nombre))
                p["img"] = salidas[0]
                if len(salidas) > 1:
                    p["imgs"] = salidas
                elif "imgs" in p:
                    del p["imgs"]
                print("%-28s %-12s %6.1f KB" % (p["nombre"], "tuya", peso / 1024))
                continue

            crudas = []
            for clave in claves:
                if crudas:
                    break
                una = os.path.join(IMG, "raw-" + clave + ".png")
                if os.path.exists(una):
                    crudas.append(una)
                n = 1
                while os.path.exists(os.path.join(IMG, "raw-%s-%d.png" % (clave, n))):
                    crudas.append(os.path.join(IMG, "raw-%s-%d.png" % (clave, n)))
                    n += 1

            if crudas:
                salidas, peso = [], 0
                for i, cruda in enumerate(crudas):
                    nombre = slug(p["nombre"]) + ("" if i == 0 else "-%d" % (i + 1)) + ".jpg"
                    peso += de_captura(cruda, os.path.join(IMG, nombre))
                    salidas.append(con_version("img/" + nombre))
                p["img"] = salidas[0]
                if len(salidas) > 1:
                    p["imgs"] = salidas
                elif "imgs" in p:
                    del p["imgs"]
                origen = "%d captura%s" % (len(salidas), "s" if len(salidas) > 1 else "")
            elif os.path.exists(destino):
                p["img"] = con_version("img/" + nombre_archivo)
                # Ya tiene portada y no hay capturas nuevas: no se toca. Sin esto,
                # correr el script dos veces pisaba las capturas con el dibujo.
                peso = os.path.getsize(destino)
                origen = "sin cambios"
            else:
                peso = generada(p, destino)
                p["img"] = con_version("img/" + nombre_archivo)
                if "imgs" in p:
                    del p["imgs"]
                origen = "dibujada"

            print("%-28s %-12s %6.1f KB" % (p["nombre"], origen, peso / 1024))

    # Se re-sella todo al final: asi las que no se regeneraron esta vez
    # tambien quedan con la version correcta de su archivo.
    for grupo in datos["grupos"]:
        for p in grupo["items"]:
            if p.get("img"):
                p["img"] = con_version(p["img"].split("?")[0])
            if p.get("imgs"):
                p["imgs"] = [con_version(i.split("?")[0]) for i in p["imgs"]]

    io.open(ruta_json, "w", encoding="utf-8", newline="\n").write(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n")
    print("\nproyectos.json actualizado con el campo img")


def escribir_privados_js():
    """Copia privados.json a privados.js.

    La home se abre como file:// y ahi Firefox no deja leer otro archivo local
    con fetch, pero si deja cargar un <script>. Por eso la misma lista va
    tambien como archivo .js, que es lo que la home termina usando.
    """
    origen = os.path.join(BASE, "privados.json")
    if not os.path.exists(origen):
        return
    datos = io.open(origen, encoding="utf-8").read().strip()
    nl = chr(10)
    salida = nl.join([
        "// Generado por tools/portadas.py a partir de privados.json.",
        "// No se publica: la home lo lee como script porque file:// no deja",
        "// leer archivos locales con fetch.",
        "window.PRIVADOS = " + datos + ";",
        "",
    ])
    destino = os.path.join(BASE, "privados.js")
    io.open(destino, "w", encoding="utf-8", newline=nl).write(salida)
    print("== privados.js escrito para la home local")


if __name__ == "__main__":
    main()
