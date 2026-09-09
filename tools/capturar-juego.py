# -*- coding: utf-8 -*-
"""Captura pantallas de un juego animado.

`chrome --screenshot` no sirve para los juegos: dibujan con requestAnimationFrame sin
parar, así que el navegador nunca considera que la página "terminó" y la captura no llega
nunca. Acá se habla con Chrome por su protocolo de depuración, que permite pedir la
captura en el momento que uno quiera y, de paso, ejecutar JavaScript para llegar al estado
que interesa: no la portada, sino la partida ya empezada.

Cliente WebSocket mínimo hecho a mano para no sumar dependencias.

Uso:
    py -3 capturar-juego.py <url> <destino> [--ancho N] [--alto N]
                            [--paso "espera:2000"] [--paso "js:document.querySelector(...).click()"]
                            [--paso "captura:nombre"]
"""
import base64, json, os, socket, struct, subprocess, sys, time, urllib.request

CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
PUERTO = 9333


class Ws:
    """Lo mínimo del protocolo WebSocket para hablar con Chrome: handshake y frames."""

    def __init__(self, url):
        resto = url.split('://', 1)[1]
        hostpuerto, _, ruta = resto.partition('/')
        host, _, puerto = hostpuerto.partition(':')
        self.s = socket.create_connection((host, int(puerto or 80)), timeout=30)
        clave = base64.b64encode(os.urandom(16)).decode()
        pedido = (
            'GET /%s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
            'Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n' % (ruta, hostpuerto, clave))
        self.s.sendall(pedido.encode())
        datos = b''
        while b'\r\n\r\n' not in datos:
            datos += self.s.recv(4096)
        self.sobra = datos.split(b'\r\n\r\n', 1)[1]
        self.id = 0

    def enviar(self, metodo, **params):
        self.id += 1
        cuerpo = json.dumps({'id': self.id, 'method': metodo, 'params': params}).encode()
        cab = bytearray([0x81])
        n = len(cuerpo)
        mascara = os.urandom(4)
        if n < 126:
            cab.append(0x80 | n)
        elif n < 65536:
            cab.append(0x80 | 126); cab += struct.pack('>H', n)
        else:
            cab.append(0x80 | 127); cab += struct.pack('>Q', n)
        cab += mascara
        cab += bytes(b ^ mascara[i % 4] for i, b in enumerate(cuerpo))
        self.s.sendall(bytes(cab))
        return self.id

    def _leer(self, n):
        while len(self.sobra) < n:
            trozo = self.s.recv(65536)
            if not trozo:
                raise IOError('la conexion se corto')
            self.sobra += trozo
        salida, self.sobra = self.sobra[:n], self.sobra[n:]
        return salida

    def recibir(self):
        b1, b2 = self._leer(2)
        largo = b2 & 0x7F
        if largo == 126:
            largo = struct.unpack('>H', self._leer(2))[0]
        elif largo == 127:
            largo = struct.unpack('>Q', self._leer(8))[0]
        return json.loads(self._leer(largo).decode('utf-8', 'replace'))

    def esperar(self, id_pedido, limite=40):
        fin = time.time() + limite
        while time.time() < fin:
            m = self.recibir()
            if m.get('id') == id_pedido:
                return m
        raise TimeoutError('Chrome no contesto el pedido %d' % id_pedido)

    def pedir(self, metodo, **params):
        return self.esperar(self.enviar(metodo, **params))


def abrir_chrome(perfil, ancho, alto):
    p = subprocess.Popen(
        [CHROME, '--headless=new', '--disable-gpu', '--no-sandbox', '--mute-audio',
         '--hide-scrollbars', '--remote-debugging-port=%d' % PUERTO,
         '--user-data-dir=%s' % perfil, '--window-size=%d,%d' % (ancho, alto), 'about:blank'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    fin = time.time() + 25
    while time.time() < fin:
        try:
            con = urllib.request.urlopen('http://127.0.0.1:%d/json' % PUERTO, timeout=2)
            for t in json.loads(con.read().decode()):
                if t.get('type') == 'page' and t.get('webSocketDebuggerUrl'):
                    return p, t['webSocketDebuggerUrl']
        except Exception:
            time.sleep(0.4)
    p.kill()
    raise RuntimeError('Chrome no abrio el puerto de depuracion')


def main():
    if len(sys.argv) < 3:
        print(__doc__); return 1
    url, destino = sys.argv[1], sys.argv[2]
    ancho, alto, pasos = 1280, 800, []
    i = 3
    while i < len(sys.argv):
        a = sys.argv[i]
        if a == '--ancho':   ancho = int(sys.argv[i+1]); i += 2
        elif a == '--alto':  alto = int(sys.argv[i+1]); i += 2
        elif a == '--paso':  pasos.append(sys.argv[i+1]); i += 2
        else: i += 1

    os.makedirs(destino, exist_ok=True)
    perfil = os.path.join(os.environ.get('TEMP', '.'), 'perfil-capturas')
    proc, ws_url = abrir_chrome(perfil, ancho, alto)
    try:
        ws = Ws(ws_url)
        ws.pedir('Page.enable')
        ws.pedir('Runtime.enable')
        ws.pedir('Emulation.setDeviceMetricsOverride',
                 width=ancho, height=alto, deviceScaleFactor=1, mobile=False)
        ws.pedir('Page.navigate', url=url)
        time.sleep(3)

        hechas = []
        i_paso = 0
        while i_paso < len(pasos):
            paso = pasos[i_paso]
            i_paso += 1
            clase, _, valor = paso.partition(':')
            if clase == 'espera':
                time.sleep(int(valor) / 1000.0)
            elif clase == 'js':
                r = ws.pedir('Runtime.evaluate', expression=valor, awaitPromise=True,
                             returnByValue=True)
                err = r.get('result', {}).get('exceptionDetails')
                if err:
                    print('  js con error:', err.get('text'))
            elif clase in ('clickEl', 'apretarEl'):
                # Adivinar coordenadas a ojo falla en cuanto cambia el tamaño de ventana:
                # acá se le pregunta al navegador dónde quedó el elemento.
                sel, _, ms = valor.partition('|')
                r = ws.pedir('Runtime.evaluate', returnByValue=True, expression="""
                    (() => { const e = document.querySelector(%s);
                      if (!e) return null;
                      const r = e.getBoundingClientRect();
                      return {x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2),
                              visible: r.width > 0 && r.height > 0}; })()
                """ % json.dumps(sel))
                pos = r.get('result', {}).get('result', {}).get('value')
                if not pos or not pos.get('visible'):
                    print('  no encontre (o no se ve):', sel); continue
                pasos.insert(i_paso,
                             '%s:%d,%d%s' % ('apretar' if clase == 'apretarEl' else 'click',
                                             pos['x'], pos['y'], ',' + ms if ms else ''))
                print('  %s en (%d,%d)' % (sel, pos['x'], pos['y']))
            elif clase in ('click', 'apretar'):
                # Un .click() por JavaScript no alcanza: los juegos escuchan pointer/mouse
                # sobre el lienzo, así que hay que mandar eventos de entrada de verdad.
                partes = [int(v) for v in valor.split(',')]
                x, y = partes[0], partes[1]
                sostener = partes[2] if len(partes) > 2 else 0
                comun = dict(x=x, y=y, button='left', clickCount=1, buttons=1)
                ws.pedir('Input.dispatchMouseEvent', type='mouseMoved', x=x, y=y)
                ws.pedir('Input.dispatchMouseEvent', type='mousePressed', **comun)
                if sostener:
                    time.sleep(sostener / 1000.0)
                ws.pedir('Input.dispatchMouseEvent', type='mouseReleased', **comun)
            elif clase == 'captura':
                r = ws.pedir('Page.captureScreenshot', format='png')
                datos = r.get('result', {}).get('data')
                if not datos:
                    print('  no vino la captura:', valor); continue
                ruta = os.path.join(destino, valor + '.png')
                with open(ruta, 'wb') as f:
                    f.write(base64.b64decode(datos))
                hechas.append((valor, os.path.getsize(ruta)))
                print('  captura %s -> %d bytes' % (valor, os.path.getsize(ruta)))
        print('listo:', len(hechas), 'capturas en', destino)
        return 0 if hechas else 1
    finally:
        proc.kill()


if __name__ == '__main__':
    sys.exit(main())
