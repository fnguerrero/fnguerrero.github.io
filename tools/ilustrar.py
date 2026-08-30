# -*- coding: utf-8 -*-
"""Portadas dibujadas para lo que no se puede fotografiar.

Hay proyectos que no tienen una pantalla web que capturar: los de escritorio, los que
piden un login que no se puede automatizar, o los que directamente ya no corren. Antes
caian en la ventana generica de `portadas.generada()`, que dibuja renglones abstractos:
sirve para no dejar un color liso, pero no dice absolutamente nada de la aplicacion.

Aca cada uno declara *que se ve adentro*: el titulo de la pantalla y unas filas con su
estado. Con eso se dibuja una ventana que se parece a la aplicacion de verdad, con datos
inventados. No es una captura y no pretende serlo; es una ilustracion fiel de lo que hace.

Correr con: py -3 tools/ilustrar.py  (o entra sola desde portadas.py)
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import portadas

ANCHO, ALTO = portadas.ANCHO, portadas.ALTO
VERDE = (34, 158, 96)
AMBAR = (198, 138, 20)
ROJO = (192, 57, 60)
GRIS = (130, 138, 148)

# Cada pantalla: el titulo de arriba y las filas, con (principal, secundario, chip, color).
# Un chip vacio deja la fila sin estado.
PANTALLAS = {
    "DevAtlas": {
        "seccion": "Catálogo",
        "titulo": "Mis aplicaciones",
        "columnas": ("APLICACIÓN", "STACK Y REPO", "AMBIENTE"),
        "filas": [
            ("Auth Service", ".NET 8 · api-auth", "producción", VERDE),
            ("Data Pipeline", "Python · etl-nightly", "staging", AMBAR),
            ("Panel de métricas", "React · panel-web", "producción", VERDE),
            ("Docs internas", "Astro · docs", "local", GRIS),
        ],
    },
    "DevDesk": {
        "seccion": "Servicios",
        "titulo": "Lo que está levantado",
        "columnas": ("SERVICIO", "DÓNDE", "ESTADO"),
        "filas": [
            ("API de facturación", ":5178 · dotnet watch", "arriba", VERDE),
            ("Base de datos", "postgres · :5432", "arriba", VERDE),
            ("Worker de colas", "rabbit · consumidor", "caído", ROJO),
            ("Front del portal", ":5173 · vite", "arriba", VERDE),
        ],
    },
    "Chequeo de Horas": {
        "seccion": "Semana",
        "titulo": "Horas cargadas",
        "columnas": ("DÍA", "CARGADO", "CONTRA LO ESPERADO"),
        "filas": [
            ("lunes 24", "8:00 de 8:00", "completo", VERDE),
            ("martes 25", "6:30 de 8:00", "faltan 1:30", AMBAR),
            ("miércoles 26", "8:00 de 8:00", "completo", VERDE),
            ("jueves 27", "0:00 de 8:00", "sin cargar", ROJO),
        ],
    },
    "Security Dashboard": {
        "seccion": "ASVS",
        "titulo": "Controles contra la API",
        "columnas": ("CONTROL", "REQUEST", "RESULTADO"),
        "filas": [
            ("V2.1.1 · largo de clave", "POST /auth/login", "pasa", VERDE),
            ("V3.3.1 · vence la sesión", "GET /yo", "pasa", VERDE),
            ("V5.3.4 · inyección SQL", "GET /clientes?q=", "falla", ROJO),
            ("V7.1.1 · logs sin secretos", "manual", "revisar", AMBAR),
        ],
    },
}


def ventana(proyecto, pantalla, destino):
    """Dibuja la ventana con su tabla y la guarda."""
    color = portadas.hex_a_rgb(proyecto["color"])
    oscuro = portadas.mezcla(color, (10, 12, 14), 0.76)
    claro = portadas.mezcla(color, (255, 255, 255), 0.06)

    im = Image.new("RGB", (ANCHO, ALTO))
    d = ImageDraw.Draw(im)
    for y in range(ALTO):
        d.line([(0, y), (ANCHO, y)], fill=portadas.mezcla(claro, oscuro, y / (ALTO - 1)))

    vidrio = (252, 252, 253)
    tinta = (22, 26, 32)
    tenue = portadas.mezcla(vidrio, tinta, 0.45)
    borde = portadas.mezcla(vidrio, tinta, 0.12)

    # La ventana termina bastante arriba del borde: abajo va el nombre del proyecto y
    # tienen que caber las cuatro filas adentro, sin que la ultima quede colgando.
    vx, vy, vw, vh = 62, 32, ANCHO - 124, ALTO - 128
    sombra = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle([vx + 5, vy + 10, vx + vw + 5, vy + vh + 10],
                                             radius=12, fill=(0, 0, 0, 80))
    im.paste(Image.alpha_composite(im.convert("RGBA"),
                                   sombra.filter(ImageFilter.GaussianBlur(10))).convert("RGB"),
             (0, 0))
    d = ImageDraw.Draw(im)

    d.rounded_rectangle([vx, vy, vx + vw, vy + vh], radius=11, fill=vidrio)
    # Barra de titulo con los tres botones y el nombre de la seccion.
    d.rounded_rectangle([vx, vy, vx + vw, vy + 30], radius=11,
                        fill=portadas.mezcla(vidrio, tinta, 0.06))
    d.rectangle([vx, vy + 20, vx + vw, vy + 30], fill=portadas.mezcla(vidrio, tinta, 0.06))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([vx + 14 + i * 15, vy + 11, vx + 22 + i * 15, vy + 19], fill=c)
    f_chico = ImageFont.truetype(portadas.FUENTE_NORMAL, 13)
    d.text((vx + 74, vy + 8), pantalla["seccion"], font=f_chico, fill=tenue)

    # Encabezado de la pantalla.
    f_tit = ImageFont.truetype(portadas.FUENTE_NEGRITA, 21)
    d.text((vx + 22, vy + 42), pantalla["titulo"], font=f_tit, fill=tinta)

    # Columnas de la tabla.
    x1, x2, x3 = vx + 22, vx + int(vw * 0.44), vx + int(vw * 0.76)
    f_col = ImageFont.truetype(portadas.FUENTE_NORMAL, 11)
    y = vy + 74
    for x, texto in zip((x1, x2, x3), pantalla["columnas"]):
        d.text((x, y), texto, font=f_col, fill=tenue)
    y += 20
    d.line([(vx + 18, y), (vx + vw - 18, y)], fill=borde, width=1)

    # Filas.
    f_uno = ImageFont.truetype(portadas.FUENTE_NEGRITA, 15)
    f_dos = ImageFont.truetype(portadas.FUENTE_NORMAL, 14)
    f_chip = ImageFont.truetype(portadas.FUENTE_NEGRITA, 12)
    alto_fila = 32
    for i, (uno, dos, chip, tono) in enumerate(pantalla["filas"]):
        fy = y + 10 + i * alto_fila
        if i % 2 == 0:
            d.rectangle([vx + 10, fy - 6, vx + vw - 10, fy + alto_fila - 12],
                        fill=portadas.mezcla(vidrio, color, 0.05))
        d.rounded_rectangle([vx + 10, fy - 6, vx + 13, fy + alto_fila - 12], radius=2,
                            fill=tono)
        d.text((x1, fy), uno, font=f_uno, fill=tinta)
        d.text((x2, fy + 1), dos, font=f_dos, fill=tenue)
        if chip:
            largo = int(d.textlength(chip, font=f_chip))
            d.rounded_rectangle([x3, fy - 1, x3 + largo + 20, fy + 21], radius=10,
                                fill=portadas.mezcla(vidrio, tono, 0.16))
            d.text((x3 + 10, fy + 3), chip, font=f_chip, fill=portadas.mezcla(tono, tinta, 0.25))
        if i < len(pantalla["filas"]) - 1:
            d.line([(vx + 18, fy + alto_fila - 12), (vx + vw - 18, fy + alto_fila - 12)],
                   fill=borde, width=1)

    # Nombre y bajada, abajo del todo.
    f_nombre = ImageFont.truetype(portadas.FUENTE_NEGRITA, 34)
    f_tag = ImageFont.truetype(portadas.FUENTE_NORMAL, 18)
    d.text((30, ALTO - 74), proyecto["nombre"], font=f_nombre, fill=(255, 255, 255))
    if proyecto.get("tag"):
        d.text((32, ALTO - 34), proyecto["tag"], font=f_tag, fill=(232, 236, 241))

    im.save(destino, "JPEG", quality=88, optimize=True, progressive=True)
    return os.path.getsize(destino)


# CelConnect no es una tabla: lo que muestra es el telefono adentro de la pantalla de la
# PC. Va por su propia funcion en vez de forzarlo al molde de arriba.
def espejo(proyecto, destino):
    """El celular espejado dentro de una ventana de escritorio."""
    color = portadas.hex_a_rgb(proyecto["color"])
    oscuro = portadas.mezcla(color, (8, 10, 12), 0.80)
    claro = portadas.mezcla(color, (255, 255, 255), 0.08)

    im = Image.new("RGB", (ANCHO, ALTO))
    d = ImageDraw.Draw(im)
    for y in range(ALTO):
        d.line([(0, y), (ANCHO, y)], fill=portadas.mezcla(claro, oscuro, y / (ALTO - 1)))

    vidrio = (250, 251, 252)
    tinta = (22, 26, 32)
    tenue = portadas.mezcla(vidrio, tinta, 0.45)

    vx, vy, vw, vh = 52, 26, ANCHO - 104, ALTO - 118
    sombra = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle([vx + 5, vy + 10, vx + vw + 5, vy + vh + 10],
                                             radius=12, fill=(0, 0, 0, 85))
    im.paste(Image.alpha_composite(im.convert("RGBA"),
                                   sombra.filter(ImageFilter.GaussianBlur(10))).convert("RGB"),
             (0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([vx, vy, vx + vw, vy + vh], radius=11, fill=vidrio)
    d.rounded_rectangle([vx, vy, vx + vw, vy + 28], radius=11,
                        fill=portadas.mezcla(vidrio, tinta, 0.06))
    d.rectangle([vx, vy + 18, vx + vw, vy + 28], fill=portadas.mezcla(vidrio, tinta, 0.06))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([vx + 14 + i * 15, vy + 10, vx + 22 + i * 15, vy + 18], fill=c)
    d.text((vx + 74, vy + 7), "Motorola · espejado", font=ImageFont.truetype(portadas.FUENTE_NORMAL, 13),
           fill=tenue)

    # El telefono, parado en el centro de la ventana.
    tw, th = 104, 186
    tx = vx + vw - tw - 46
    ty = vy + 42
    d.rounded_rectangle([tx - 5, ty - 5, tx + tw + 5, ty + th + 5], radius=16, fill=(28, 32, 38))
    pantalla = portadas.mezcla(color, (18, 22, 28), 0.55)
    d.rounded_rectangle([tx, ty, tx + tw, ty + th], radius=12, fill=pantalla)
    d.rounded_rectangle([tx + 38, ty + 4, tx + tw - 38, ty + 10], radius=3, fill=(28, 32, 38))
    # Una grilla de aplicaciones adentro.
    for fila in range(4):
        for col in range(3):
            ax = tx + 14 + col * 27
            ay = ty + 26 + fila * 33
            d.rounded_rectangle([ax, ay, ax + 20, ay + 20], radius=6,
                                fill=portadas.mezcla(pantalla, (255, 255, 255),
                                                     0.16 + 0.05 * ((fila + col) % 3)))
    d.rounded_rectangle([tx + 26, ty + th - 14, tx + tw - 26, ty + th - 10], radius=2,
                        fill=portadas.mezcla(pantalla, (255, 255, 255), 0.35))

    # A la izquierda, lo que hace: doble clic y esta.
    f_tit = ImageFont.truetype(portadas.FUENTE_NEGRITA, 20)
    f_txt = ImageFont.truetype(portadas.FUENTE_NORMAL, 14)
    d.text((vx + 26, vy + 50), "Conectado por WiFi", font=f_tit, fill=tinta)
    lineas = ["Sin cables y sin terminal.", "Doble clic en el acceso directo.",
              "Se maneja con mouse y teclado."]
    for i, t in enumerate(lineas):
        d.ellipse([vx + 28, vy + 88 + i * 26, vx + 34, vy + 94 + i * 26],
                  fill=portadas.mezcla(vidrio, color, 0.75))
        d.text((vx + 44, vy + 82 + i * 26), t, font=f_txt, fill=tenue)

    f_nombre = ImageFont.truetype(portadas.FUENTE_NEGRITA, 34)
    f_tag = ImageFont.truetype(portadas.FUENTE_NORMAL, 18)
    d.text((30, ALTO - 74), proyecto["nombre"], font=f_nombre, fill=(255, 255, 255))
    if proyecto.get("tag"):
        d.text((32, ALTO - 34), proyecto["tag"], font=f_tag, fill=(232, 236, 241))

    im.save(destino, "JPEG", quality=88, optimize=True, progressive=True)
    return os.path.getsize(destino)


APARTE = {"CelConnect": espejo}


def hay_para(nombre):
    return nombre in PANTALLAS or nombre in APARTE


def dibujar(proyecto, destino):
    if proyecto["nombre"] in APARTE:
        return APARTE[proyecto["nombre"]](proyecto, destino)
    return ventana(proyecto, PANTALLAS[proyecto["nombre"]], destino)


def main():
    import json
    import io
    hechos = 0
    for archivo in ("proyectos.json", "privados.json"):
        ruta = os.path.join(portadas.BASE, archivo)
        if not os.path.exists(ruta):
            continue
        datos = json.load(io.open(ruta, encoding="utf-8"))
        for grupo in datos["grupos"]:
            for p in grupo["items"]:
                if not hay_para(p["nombre"]):
                    continue
                destino = os.path.join(portadas.IMG, portadas.slug(p["nombre"]) + ".jpg")
                peso = dibujar(p, destino)
                print("%-22s %6.1f KB" % (p["nombre"], peso / 1024))
                hechos += 1
    print("%d portadas dibujadas" % hechos)


if __name__ == "__main__":
    main()
