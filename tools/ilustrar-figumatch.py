# -*- coding: utf-8 -*-
"""Dibuja la portada de Figumatch.

La app no se puede capturar por dentro (su base de datos no responde), asi que
en vez de mostrar la pantalla de entrada se ilustra lo que hace: dos albumes
enfrentados, uno con repetidas y otro con faltantes, y el cruce en el medio.

Correr con: py -3 tools/ilustrar-figumatch.py
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import portadas

ANCHO, ALTO = portadas.ANCHO, portadas.ALTO
COLOR = portadas.hex_a_rgb("#B8455E")
NEGRITA = portadas.FUENTE_NEGRITA
NORMAL = portadas.FUENTE_NORMAL


def album(d, x, y, ancho, alto, marcadas, tinte, marca):
    """Un album: grilla de figuritas, con algunas marcadas."""
    d.rounded_rectangle([x, y, x + ancho, y + alto], radius=10,
                        fill=portadas.mezcla(COLOR, (255, 255, 255), 0.92))
    cols, filas = 4, 3
    paso_x = (ancho - 22) / cols
    paso_y = (alto - 22) / filas
    f = ImageFont.truetype(NEGRITA, 13)
    for i in range(cols * filas):
        cx = x + 11 + (i % cols) * paso_x
        cy = y + 11 + (i // cols) * paso_y
        pegada = i in marcadas
        relleno = tinte if pegada else portadas.mezcla(COLOR, (255, 255, 255), 0.82)
        d.rounded_rectangle([cx + 3, cy + 3, cx + paso_x - 5, cy + paso_y - 5],
                            radius=5, fill=relleno)
        if pegada:
            t = marca
            caja = d.textbbox((0, 0), t, font=f)
            d.text((cx + 3 + (paso_x - 8 - (caja[2] - caja[0])) / 2,
                    cy + 3 + (paso_y - 8 - (caja[3] - caja[1])) / 2 - caja[1]),
                   t, font=f, fill=(255, 255, 255))


def main():
    oscuro = portadas.mezcla(COLOR, (10, 12, 14), 0.74)
    claro = portadas.mezcla(COLOR, (255, 255, 255), 0.05)

    im = Image.new("RGB", (ANCHO, ALTO))
    d = ImageDraw.Draw(im)
    for y in range(ALTO):
        d.line([(0, y), (ANCHO, y)], fill=portadas.mezcla(claro, oscuro, y / (ALTO - 1)))

    # Sombra de los dos albumes.
    sombra = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sombra)
    for x in (52, 372):
        ds.rounded_rectangle([x + 4, 78, x + 220, 258], radius=10, fill=(0, 0, 0, 80))
    im.paste(Image.alpha_composite(im.convert("RGBA"),
                                   sombra.filter(ImageFilter.GaussianBlur(10))).convert("RGB"),
             (0, 0))
    d = ImageDraw.Draw(im)

    verde = (34, 158, 96)
    naranja = (214, 122, 42)
    album(d, 52, 74, 216, 180, {0, 2, 5, 6, 9}, verde, "2")      # repetidas
    album(d, 372, 74, 216, 180, {1, 3, 4, 8, 10}, naranja, "?")  # faltantes

    # Rotulos de cada album.
    f_rot = ImageFont.truetype(NORMAL, 17)
    d.text((52, 50), "tus repetidas", font=f_rot, fill=(240, 235, 238))
    d.text((372, 50), "lo que le falta", font=f_rot, fill=(240, 235, 238))

    # El cruce del medio: dos flechas que se cambian una por otra.
    cx, cy = ANCHO / 2, 164
    for signo, color in ((1, verde), (-1, naranja)):
        y = cy - 16 * signo
        d.line([(cx - 44, y), (cx + 44, y)], fill=color, width=5)
        punta = cx + 44 if signo > 0 else cx - 44
        paso = -11 if signo > 0 else 11
        d.polygon([(punta, y), (punta + paso, y - 8), (punta + paso, y + 8)], fill=color)

    # Nombre y bajada.
    f_nombre = ImageFont.truetype(NEGRITA, 36)
    f_tag = ImageFont.truetype(NORMAL, 19)
    d.text((36, ALTO - 84), "Figumatch", font=f_nombre, fill=(255, 255, 255))
    d.text((38, ALTO - 40), "Intercambio de figuritas", font=f_tag, fill=(235, 238, 242))

    destino = os.path.join(portadas.IMG, "figumatch.jpg")
    im.save(destino, "JPEG", quality=88, optimize=True, progressive=True)
    print("figumatch.jpg %.1f KB" % (os.path.getsize(destino) / 1024))


if __name__ == "__main__":
    main()
