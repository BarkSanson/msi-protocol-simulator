import json
import threading
from enum import Enum

import paho.mqtt.client as paho

from tipo_peticion import TipoPeticion
from evento import Evento, TipoEventoProcesador
from evento_provider import EventoProvider
from administrador_mensajes import AdministradorMensajes

HOST = "127.0.0.1"
PORT = 8000
KEEP_ALIVE = 60

MSI = "msi"
ID = "P1"
VALOR_NUL0 = f"{ID}-0"


class EstadoCacheCpu(Enum):
    MODIFICADO = 0
    COMPARTIDO = 1
    INVALIDO = 2


class CacheCpu:
    def __init__(self):
        self.__bloques = {
            'A': (VALOR_NUL0, EstadoCacheCpu.INVALIDO),
            'B': (VALOR_NUL0, EstadoCacheCpu.INVALIDO),
            'C': (VALOR_NUL0, EstadoCacheCpu.INVALIDO),
            'D': (VALOR_NUL0, EstadoCacheCpu.INVALIDO),
            'E': (VALOR_NUL0, EstadoCacheCpu.INVALIDO),
        }

    def get_bloque(self, bloque) -> (int, EstadoCacheCpu):
        return self.__bloques[bloque]

    def cambia_valor_bloque(self, bloque, valor: int):
        tupla_bloque = list(self.__bloques[bloque])
        tupla_bloque[0] = valor
        self.__bloques[bloque] = tuple(tupla_bloque)

    def cambia_estado_bloque(self, bloque, estado: EstadoCacheCpu):
        tupla_bloque = list(self.__bloques[bloque])
        tupla_bloque[1] = estado
        self.__bloques[bloque] = tuple(tupla_bloque)


class Cpu:
    def __init__(self, name: str, cache: CacheCpu, evento_provider: EventoProvider):
        self.__name = name
        self.__cache = cache
        self.__evento_provider = evento_provider

    def ejecutar_operaciones(self):
        evento = self.__evento_provider.leer_evento()
        tipo_evento = evento.tipo_evento
        bloque = evento.bloque
        valor = evento.valor
        valor_actual, estado_actual = self.__cache.get_bloque(bloque)

        while evento is not None:
            if estado_actual == EstadoCacheCpu.INVALIDO:
                if tipo_evento == TipoEventoProcesador.PR_ESC:
                    self.__cache.cambia_estado_bloque(bloque, EstadoCacheCpu.MODIFICADO)
                    AdministradorMensajes.publicar_mensaje(TipoPeticion.PETICION_LECTURA_EXCLUSIVA, bloque, self.__name)
                elif tipo_evento == TipoEventoProcesador.PR_LEC:
                    self.__cache.cambia_estado_bloque(bloque, EstadoCacheCpu.COMPARTIDO)
                    AdministradorMensajes.publicar_mensaje(TipoPeticion.PETICION_LECTURA_EXCLUSIVA, bloque, self.__name)
            elif estado_actual == EstadoCacheCpu.COMPARTIDO:
                if tipo_evento == TipoEventoProcesador.PR_ESC:
                    self.__cache.cambia_estado_bloque(bloque, EstadoCacheCpu.MODIFICADO)
                    AdministradorMensajes.publicar_mensaje(TipoPeticion.PETICION_LECTURA_EXCLUSIVA, bloque, self.__name)

    def __procesar_mensaje(self, evento, bloque, valor, origen):
        valor_actual, estado_actual = self.__cache.get_bloque(bloque)

        if origen == self.__name:
            return

        if estado_actual == EstadoCacheCpu.COMPARTIDO:
            if evento == TipoPeticion.PETICION_LECTURA_EXCLUSIVA:
                self.__cache.cambia_estado_bloque(bloque, EstadoCacheCpu.INVALIDO)
        elif estado_actual == EstadoCacheCpu.MODIFICADO:
            if evento == TipoPeticion.PETICION_LECTURA:
                AdministradorMensajes.publicar_mensaje(TipoPeticion.PETICION_LECTURA_EXCLUSIVA, bloque, self.__name)
                self.__cache.cambia_estado_bloque(bloque, EstadoCacheCpu.COMPARTIDO)
            elif evento == TipoPeticion.PETICION_LECTURA_EXCLUSIVA:
                AdministradorMensajes.publicar_mensaje(TipoPeticion.PETICION_LECTURA_EXCLUSIVA, bloque, self.__name)

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = json.loads(msg.payload)

        _, tipo_peticion = topic.split('/')
        bloque = payload["bloque"]
        valor = None
        if "valor" in payload:
            valor = payload["valor"]
        origen = payload["origen"]

        pro_msg = threading.Thread(target=self.__procesar_mensaje, args=[tipo_peticion, bloque, valor, origen])
        pro_msg.start()
        client.publish('pong', 'ack', 0)


def main():
    cache = CacheCpu()
    evento_provider = EventoProvider(f"{ID}.txt")
    cpu = Cpu(ID, cache, evento_provider)
    client = paho.Client()
    client.on_message = cpu.on_message

    client.connect(HOST, PORT, KEEP_ALIVE)

    print(f"Connected to {HOST}:{PORT}")

    client.subscribe(f"{MSI}/#", 0)

    while client.loop() == 0:
        pass


if __name__ == '__main__':
    main()
