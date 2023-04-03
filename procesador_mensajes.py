from abc import ABC, abstractmethod


class ProcesadorMensajes(ABC):
    @abstractmethod
    def procesar_mensaje(self, peticion, bloque, origen, destino=None, valor=None):
        pass
