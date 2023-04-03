import sys
import random
import time
from enum import Enum

import paho.mqtt.client as paho

from administrador_mensajes import AdministradorMensajes
from evento import TipoEventoProcesador
from evento_provider import EventoProvider
from eventos_file_writer import EventosFileWriter
from procesador_mensajes import ProcesadorMensajes
from tipo_peticion import TipoPeticion

HOST = "127.0.0.1"
PORT = 8000
KEEP_ALIVE = 60

MSI = "msi"
ID = "P1"
VALOR_NULO = f"{ID}-0"

SEED = 1000


class EstadoCacheCpu(Enum):
    MODIFICADO = 0
    COMPARTIDO = 1
    INVALIDO = 2


class CacheCpu:
    def __init__(self):
        self.__bloques = {
            'A': (VALOR_NULO, EstadoCacheCpu.INVALIDO),
            'B': (VALOR_NULO, EstadoCacheCpu.INVALIDO),
            'C': (VALOR_NULO, EstadoCacheCpu.INVALIDO),
            'D': (VALOR_NULO, EstadoCacheCpu.INVALIDO),
            'E': (VALOR_NULO, EstadoCacheCpu.INVALIDO),
        }

    def get_bloque(self, bloque) -> (str, EstadoCacheCpu):
        return self.__bloques[bloque]

    def cambia_valor_bloque(self, bloque, valor: str):
        tupla_bloque = list(self.__bloques[bloque])
        tupla_bloque[0] = valor
        self.__bloques[bloque] = tuple(tupla_bloque)

    def cambia_estado_bloque(self, bloque, estado: EstadoCacheCpu):
        tupla_bloque = list(self.__bloques[bloque])
        tupla_bloque[1] = estado
        self.__bloques[bloque] = tuple(tupla_bloque)


class Cpu(ProcesadorMensajes):
    def __init__(self, name: str, cache: CacheCpu, evento_provider: EventoProvider):
        self.__name = name
        self.__cache = cache
        self.__evento_provider = evento_provider

    def ejecutar_operaciones(self):
        evento = self.__evento_provider.leer_evento()

        while evento is not None:
            tipo_evento = evento.tipo_evento
            bloque = evento.bloque
            valor = evento.valor
            valor_actual, estado_actual = self.__cache.get_bloque(bloque)

            if estado_actual == EstadoCacheCpu.INVALIDO:
                if tipo_evento == TipoEventoProcesador.PR_ESC:
                    AdministradorMensajes.publicar_mensaje(TipoPeticion.PETICION_LECTURA_EXCLUSIVA.value, bloque, self.__name)

                    self.esperar_por_estado(bloque, EstadoCacheCpu.MODIFICADO)

                    EventosFileWriter.escribir_evento(
                        fichero=f"{self.__name}-out.txt",
                        evento=TipoEventoProcesador.PR_ESC.value,
                        bloque=bloque,
                        valor=valor)
                elif tipo_evento == TipoEventoProcesador.PR_LEC:
                    AdministradorMensajes.publicar_mensaje(TipoPeticion.PETICION_LECTURA.value, bloque, self.__name)

                    self.esperar_por_estado(bloque, EstadoCacheCpu.COMPARTIDO)
            elif estado_actual == EstadoCacheCpu.COMPARTIDO:
                if tipo_evento == TipoEventoProcesador.PR_ESC:
                    AdministradorMensajes.publicar_mensaje(TipoPeticion.PETICION_LECTURA_EXCLUSIVA.value, bloque, self.__name)

                    self.esperar_por_estado(bloque, EstadoCacheCpu.MODIFICADO)

                    EventosFileWriter.escribir_evento(
                        fichero=f"{self.__name}-out.txt",
                        evento=TipoEventoProcesador.PR_ESC.value,
                        bloque=bloque,
                        valor=valor)
                elif tipo_evento == TipoEventoProcesador.PR_LEC:
                    EventosFileWriter.escribir_evento(
                        fichero=f"{self.__name}-out.txt",
                        evento=TipoEventoProcesador.PR_LEC.value,
                        bloque=bloque,
                        valor=valor_actual)

            elif estado_actual == EstadoCacheCpu.MODIFICADO:
                self.__cache.cambia_valor_bloque(bloque, valor)
                if tipo_evento == TipoEventoProcesador.PR_ESC:
                    EventosFileWriter.escribir_evento(
                        fichero=f"{self.__name}-out.txt",
                        evento=TipoEventoProcesador.PR_ESC.value,
                        bloque=bloque,
                        valor=valor)


            evento = self.__evento_provider.leer_evento()

            sleep_time = random.randint(1, 10)
            # time.sleep(sleep_time)
            time.sleep(1)

    def esperar_por_estado(self, bloque, estado: EstadoCacheCpu):
        _, estado_actual = self.__cache.get_bloque(bloque)

        while estado_actual != estado:
            _, estado_actual = self.__cache.get_bloque(bloque)

    def procesar_mensaje(self, peticion, bloque, origen, destino=None, valor=None):
        valor_actual, estado_actual = self.__cache.get_bloque(bloque)

        if origen == self.__name:
            return

        if estado_actual == EstadoCacheCpu.COMPARTIDO:
            if peticion == TipoPeticion.PETICION_LECTURA_EXCLUSIVA.value:
                self.__cache.cambia_estado_bloque(bloque, EstadoCacheCpu.INVALIDO)
            elif peticion == TipoPeticion.RESPUESTA_BLOQUE_EXCLUSIVA.value and destino == self.__name:
                self.__cache.cambia_estado_bloque(bloque, EstadoCacheCpu.MODIFICADO)
                # self.__cache.cambia_valor_bloque(bloque, valor)
        elif estado_actual == EstadoCacheCpu.MODIFICADO:
            if peticion == TipoPeticion.PETICION_LECTURA.value:
                AdministradorMensajes.publicar_mensaje(
                    TipoPeticion.RESPUESTA_BLOQUE_LECTURA.value,
                    bloque,
                    self.__name,
                    origen,
                    valor_actual
                )
                self.__cache.cambia_estado_bloque(bloque, EstadoCacheCpu.COMPARTIDO)
            elif peticion == TipoPeticion.PETICION_LECTURA_EXCLUSIVA.value:
                AdministradorMensajes.publicar_mensaje(
                    TipoPeticion.RESPUESTA_BLOQUE_EXCLUSIVA.value,
                    bloque,
                    self.__name,
                    origen,
                    valor_actual
                )
        elif estado_actual == EstadoCacheCpu.INVALIDO:
            if peticion == TipoPeticion.RESPUESTA_BLOQUE_EXCLUSIVA.value \
                    or peticion == TipoPeticion.RESPUESTA_BLOQUE_LECTURA.value:
                if destino == self.__name:
                    if peticion == TipoPeticion.RESPUESTA_BLOQUE_EXCLUSIVA.value:
                        self.__cache.cambia_estado_bloque(bloque, EstadoCacheCpu.MODIFICADO)
                    elif peticion == TipoPeticion.RESPUESTA_BLOQUE_LECTURA.value:
                        self.__cache.cambia_estado_bloque(bloque, EstadoCacheCpu.COMPARTIDO)

                    self.__cache.cambia_valor_bloque(bloque, valor)

                    EventosFileWriter.escribir_evento(
                        fichero=f"{self.__name}-out.txt",
                        evento=TipoEventoProcesador.PR_LEC.value,
                        bloque=bloque,
                        valor=valor
                    )


def main():
    random.seed(SEED)

    cache = CacheCpu()
    evento_provider = EventoProvider(f"{ID}.txt")
    cpu = Cpu(ID, cache, evento_provider)
    msg_admin = AdministradorMensajes(cpu)

    client = paho.Client()
    client.connect(HOST, PORT, KEEP_ALIVE)

    print(f"Connected to {HOST}:{PORT}")

    client.subscribe(f"{MSI}/#", 0)

    client.on_message = msg_admin.on_message

    client.loop_start()

    cpu.ejecutar_operaciones()


if __name__ == '__main__':
    main()
