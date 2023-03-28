from abc import ABC, abstractmethod


class ProcesadorMensajes(ABC):
    @abstractmethod
    def procesar_mensaje(self, evento, bloque, origen, valor=None):
        pass
