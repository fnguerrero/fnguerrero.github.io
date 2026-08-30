# -*- coding: utf-8 -*-
"""Genera el icono del taller: favicon.ico multi-tamano y los PNG del sitio.

El emoji se dibuja con Segoe UI Emoji a color (embedded_color) sobre el verde
de la pagina, en un cuadrado redondeado. Correr con: py -3 tools/generar-icono.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.abspath(os.path.join(AQUI, ".."))

VERDE = (31, 95, 75, 255)      # --accent de la pagina
EMOJI = "\U0001F9F0"           # caja de herramientas
FUENTE = r"C:\Windows\Fonts\seguiemj.ttf"
LADO = 512


def lienzo(lado):
    """Cuadrado redondeado con el verde de la pagina."""
    img = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, lado - 1, lado - 1], radius=int(lado * 0.22), fill=VERDE)
    return img


def con_emoji(lado):
    img = lienzo(lado)
    # Segoe UI Emoji solo trae bitmaps de 109 px: se dibuja en ese tamano y se escala.
    base = 109
    capa = Image.new("RGBA", (base * 2, base * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    fuente = ImageFont.truetype(FUENTE, base)
    caja = d.textbbox((0, 0), EMOJI, font=fuente, embedded_color=True)
    d.text(((capa.width - (caja[2] - caja[0])) / 2 - caja[0],
            (capa.height - (caja[3] - caja[1])) / 2 - caja[1]),
           EMOJI, font=fuente, embedded_color=True)

    # Recorta lo dibujado y lo centra ocupando ~64% del icono.
    recorte = capa.crop(capa.getbbox())
    destino = int(lado * 0.64)
    escala = destino / max(recorte.size)
    recorte = recorte.resize((max(1, int(recorte.width * escala)),
                              max(1, int(recorte.height * escala))), Image.LANCZOS)
    img.alpha_composite(recorte, ((lado - recorte.width) // 2, (lado - recorte.height) // 2))
    return img


def main():
    grande = con_emoji(LADO)

    ico = os.path.join(SALIDA, "favicon.ico")
    grande.save(ico, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("favicon.ico", os.path.getsize(ico), "bytes")

    for lado, nombre in [(180, "apple-touch-icon.png"), (512, "icono-512.png")]:
        p = os.path.join(SALIDA, nombre)
        grande.resize((lado, lado), Image.LANCZOS).save(p)
        print(nombre, os.path.getsize(p), "bytes")


if __name__ == "__main__":
    main()
