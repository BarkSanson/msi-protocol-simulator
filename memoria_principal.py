from enum import Enum

import paho.mqtt.client as paho

from administrador_mensajes import AdministradorMensajes
from procesador_mensajes import ProcesadorMensajes
from tipo_peticion import TipoPeticion

HOST = "127.0.0.1"
PORT = 8000
KEEP_ALIVE = 60

MSI = "msi"

MEM = "MEM"
VALOR_NULO = "MEM-0"


class EstadoCacheMemoria(Enum):
    INVALIDO = 0
    VALIDO = 1


class CacheMemoria:
    def __init__(self):
        self.__bloques = {
            'A': (VALOR_NULO, EstadoCacheMemoria.VALIDO),
            'B': (VALOR_NULO, EstadoCacheMemoria.VALIDO),
            'C': (VALOR_NULO, EstadoCacheMemoria.VALIDO),
            'D': (VALOR_NULO, EstadoCacheMemoria.VALIDO),
            'E': (VALOR_NULO, EstadoCacheMemoria.VALIDO),
        }

    def get_bloque(self, bloque) -> (str, EstadoCacheMemoria):
        return self.__bloques[bloque]

    def cambia_valor_bloque(self, bloque, valor: str):
        tupla_bloque = list(self.__bloques[bloque])
        tupla_bloque[0] = valor
        self.__bloques[bloque] = tuple(tupla_bloque)

    def cambia_estado_bloque(self, bloque, estado: EstadoCacheMemoria):
        tupla_bloque = list(self.__bloques[bloque])
        tupla_bloque[1] = estado
        self.__bloques[bloque] = tuple(tupla_bloque)


class MemoriaPrincipal(ProcesadorMensajes):
    def __init__(self, cache: CacheMemoria):
        self.__cache = cache

    def procesar_mensaje(self, peticion, bloque, origen, destino=None, valor=None):
        valor_actual, estado_actual = self.__cache.get_bloque(bloque)

        if origen == MEM:
            return

        if estado_actual == EstadoCacheMemoria.VALIDO:
            if peticion == TipoPeticion.PETICION_LECTURA.value:
                AdministradorMensajes.publicar_mensaje(
                    TipoPeticion.RESPUESTA_BLOQUE_LECTURA.value,
                    bloque,
                    MEM,
                    origen,
                    valor_actual)
            elif peticion == TipoPeticion.PETICION_LECTURA_EXCLUSIVA.value:
                AdministradorMensajes.publicar_mensaje(
                    TipoPeticion.RESPUESTA_BLOQUE_EXCLUSIVA.value,
                    bloque,
                    MEM,
                    origen,
                    valor_actual)
                self.__cache.cambia_estado_bloque(bloque, EstadoCacheMemoria.INVALIDO)
        elif estado_actual == EstadoCacheMemoria.INVALIDO:
            if peticion == TipoPeticion.RESPUESTA_BLOQUE_LECTURA.value:
                self.__cache.cambia_estado_bloque(bloque, EstadoCacheMemoria.VALIDO)
                self.__cache.cambia_valor_bloque(bloque, valor)


def main():
    cache = CacheMemoria()
    memoria = MemoriaPrincipal(cache)
    msg_admin = AdministradorMensajes(memoria)

    client = paho.Client()

    client.connect(HOST, PORT, KEEP_ALIVE)

    print(f"Connected to {HOST}:{PORT}!")

    client.subscribe(f"{MSI}/#", 0)

    client.on_message = msg_admin.on_message

    client.loop_forever()


if __name__ == '__main__':
    main()
