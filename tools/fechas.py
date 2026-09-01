# -*- coding: utf-8 -*-
"""Anota en el indice cuando se toco cada proyecto por ultima vez.

El dato sale del ultimo commit del repositorio local, no de la API de GitHub: asi funciona
igual para los privados, no depende de la red y no gasta el limite de pedidos por hora.
Ademas mide lo que hay en el disco, que es lo que a Nico le interesa saber.

Escribe el campo `tocado` (AAAA-MM-DD) en proyectos.json y privados.json. La pagina lo
convierte en "hace 3 dias" al dibujar la tarjeta.

Correr con: py -3 tools/fechas.py
"""
import collections
import io
import json
import os
import re
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(BASE)

# Carpetas que no son proyectos.
SALTEAR = {"_archivo", "_backups", "_tools", "Archivos", "Iconos", "Pruebas", "Pendrive",
           "Nueva carpeta", "Seguridad", "Cerca"}


def git(carpeta, *args):
    try:
        r = subprocess.run(("git", "-C", carpeta) + args, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


# Cuando la carpeta no se llama como el proyecto. Solo los casos que no salen por el
# repositorio: la app se llama Focus y la carpeta quedo como Foco.
ALIAS = {"focus": "foco"}


def normalizar(texto):
    return re.sub(r"[^a-z0-9]", "", (texto or "").lower())


def fechas_del_disco():
    """Ultimo commit de cada repositorio local, indexado por repo y por nombre de carpeta."""
    salida = {}
    for nombre in os.listdir(RAIZ):
        carpeta = os.path.join(RAIZ, nombre)
        if nombre in SALTEAR or nombre.startswith(".") or not os.path.isdir(carpeta):
            continue
        if not os.path.isdir(os.path.join(carpeta, ".git")):
            continue
        fecha = git(carpeta, "log", "-1", "--format=%ad", "--date=short")
        if not fecha:
            continue
        salida[normalizar(nombre)] = fecha
        remoto = git(carpeta, "remote", "get-url", "origin") or ""
        m = re.search(r"github\.com[:/][^/]+/(.+?)(?:\.git)?/?$", remoto)
        if m:
            salida["repo:" + m.group(1).lower()] = fecha
    return salida


def main():
    fechas = fechas_del_disco()
    print("%d repositorios leidos del disco" % len([k for k in fechas if not k.startswith("repo:")]))

    for archivo in ("proyectos.json", "privados.json"):
        ruta = os.path.join(BASE, archivo)
        if not os.path.exists(ruta):
            continue
        datos = json.load(io.open(ruta, encoding="utf-8"),
                          object_pairs_hook=collections.OrderedDict)

        puestos, sin_fecha = 0, []
        for grupo in datos["grupos"]:
            for p in grupo["items"]:
                fecha = None
                if p.get("repo"):
                    m = re.search(r"github\.com/[^/]+/(.+?)/?$", p["repo"])
                    if m:
                        fecha = fechas.get("repo:" + m.group(1).lower())
                if not fecha:
                    clave = normalizar(p["nombre"])
                    fecha = fechas.get(clave) or fechas.get(ALIAS.get(clave, ""))
                if fecha:
                    p["tocado"] = fecha
                    puestos += 1
                else:
                    # Sin carpeta local no hay de donde sacar la fecha: se saca el campo
                    # viejo en vez de dejar uno que envejece sin que nadie lo note.
                    p.pop("tocado", None)
                    sin_fecha.append(p["nombre"])

        io.open(ruta, "w", encoding="utf-8", newline="").write(
            json.dumps(datos, ensure_ascii=False, indent=2) + "\n")
        print("%-16s %d con fecha%s" % (
            archivo, puestos, ", sin: " + ", ".join(sin_fecha) if sin_fecha else ""))

    # La home local no lee privados.json sino su copia en .js, asi que hay que rehacerla:
    # si no, las fechas quedan solo en el JSON y la home sigue mostrando lo viejo.
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import portadas
    portadas.escribir_privados_js()
    print("privados.js regenerado")


if __name__ == "__main__":
    main()
