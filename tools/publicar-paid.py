# -*- coding: utf-8 -*-
"""Compila Paid y deja el resultado adentro del sitio, en `paid/`.

Paid vive en su propio repositorio, que es privado. Lo que se publica es solo la
aplicacion compilada, copiada dentro de fnguerrero.github.io. Por eso el deploy es esto y
no un push al repositorio de la app.

Dos cuidados que justifican el script en vez de un copiar y pegar a mano:

  - `PAID_PUBLICO=1` deja afuera `bandeja/arranque-desde-el-mail.json`, que son facturas
    de verdad y no tienen por que estar en internet.
  - La carpeta de destino se vacia antes de copiar: Vite le pone un hash al nombre de cada
    archivo, asi que sin eso se van acumulando los de todas las versiones anteriores.

Correr con: py -3 tools/publicar-paid.py
"""
import os
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(os.path.dirname(BASE), "Paid")
DESTINO = os.path.join(BASE, "paid")


def main():
    if not os.path.isdir(APP):
        sys.exit("No esta la carpeta de Paid en %s" % APP)

    entorno = dict(os.environ, PAID_PUBLICO="1")
    print("Compilando...")
    hecho = subprocess.run("npm.cmd run build", cwd=APP, env=entorno, shell=True)
    if hecho.returncode != 0:
        sys.exit("El build fallo, no se toca nada de lo publicado.")

    dist = os.path.join(APP, "dist")
    colado = os.path.join(dist, "bandeja")
    if os.path.exists(colado):
        sys.exit("El build trajo bandeja/: son facturas reales. No se publica.")

    if os.path.exists(DESTINO):
        shutil.rmtree(DESTINO)
    shutil.copytree(dist, DESTINO)

    archivos = sum(len(f) for _, _, f in os.walk(DESTINO))
    peso = sum(os.path.getsize(os.path.join(r, f))
               for r, _, fs in os.walk(DESTINO) for f in fs)
    print("Listo: %d archivos, %.0f KB en %s" % (archivos, peso / 1024, DESTINO))
    print("Falta el commit y el push del sitio.")


if __name__ == "__main__":
    main()
