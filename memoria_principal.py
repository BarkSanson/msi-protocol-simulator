import threading
import json
from enum import Enum

import paho.mqtt.client as paho

from tipo_peticion import TipoPeticion
from administrador_mensajes import AdministradorMensajes

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

    def get_bloque(self, bloque) -> (int, EstadoCacheMemoria):
        return self.__bloques[bloque]

    def cambia_valor_bloque(self, bloque, valor: int):
        tupla_bloque = list(self.__bloques[bloque])
        tupla_bloque[0] = valor
        self.__bloques[bloque] = tuple(tupla_bloque)

    def cambia_estado_bloque(self, bloque, estado: EstadoCacheMemoria):
        tupla_bloque = list(self.__bloques[bloque])
        tupla_bloque[1] = estado
        self.__bloques[bloque] = tuple(tupla_bloque)


class MemoriaPrincipal:
    def __init__(self, cache: CacheMemoria):
        self.__cache = cache

    def __procesar_mensaje(self, evento, bloque, valor=None):
        valor_actual, estado_actual = self.__cache.get_bloque(bloque)

        if estado_actual == EstadoCacheMemoria.VALIDO:
            if evento == TipoPeticion.PETICION_LECTURA.value:
                AdministradorMensajes.publicar_mensaje(TipoPeticion.RESPUESTA_BLOQUE_LECTURA, bloque, valor_actual, MEM)
            elif evento == TipoPeticion.PETICION_LECTURA_EXCLUSIVA.value:
                AdministradorMensajes.publicar_mensaje(TipoPeticion.RESPUESTA_BLOQUE_LECTURA, bloque, valor_actual, MEM)
                self.__cache.cambia_estado_bloque(bloque, EstadoCacheMemoria.INVALIDO)
        elif estado_actual == EstadoCacheMemoria.INVALIDO:
            if evento == TipoPeticion.RESPUESTA_BLOQUE_LECTURA.value:
                self.__cache.cambia_estado_bloque(bloque, EstadoCacheMemoria.VALIDO)
                self.__cache.cambia_valor_bloque(bloque, valor)

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = json.loads(msg.payload)

        _, tipo_peticion = topic.split('/')
        bloque = payload["bloque"]
        valor = None
        if "valor" in payload:
            valor = payload["valor"]

        pro_msg = threading.Thread(target=self.__procesar_mensaje, args=[tipo_peticion, bloque, valor])
        pro_msg.start()
        client.publish('pong', 'ack', 0)


def main():
    cache = CacheMemoria()
    memoria = MemoriaPrincipal(cache)
    client = paho.Client()
    client.on_message = memoria.on_message

    client.connect(HOST, PORT, KEEP_ALIVE)

    print(f"Connected to {HOST}:{PORT}!")

    client.subscribe(f"{MSI}/#", 0)

    while client.loop() == 0:
        pass


if __name__ == '__main__':
    main()
