from enum import Enum


class TipoEventoProcesador(Enum):
    PR_LEC = "PrLec"
    PR_ESC = "PrEsc"


class Evento:
    def __init__(self, tipo_evento_procesador: TipoEventoProcesador, bloque: str, valor: str = None):
        self.__tipo_evento_procesador = tipo_evento_procesador
        self.__bloque = bloque
        self.__valor = valor

    @property
    def tipo_evento(self):
        return self.__tipo_evento_procesador

    @property
    def bloque(self):
        return self.__bloque

    @property
    def valor(self):
        return self.__valor
