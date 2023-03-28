from enum import Enum

from evento import Evento, TipoEventoProcesador


class EventoProvider:
    def __init__(self, file: str):
        with open(file, "r") as file:
            self.__operaciones = file.readlines()

    def leer_evento(self) -> None | Evento:
        if len(self.__operaciones) == 0:
            return None

        evento_string = self.__operaciones.pop()
        tipo_evento, operacion = evento_string.split(" ")

        if tipo_evento == TipoEventoProcesador.PR_LEC.value:
            # En este caso, la operación únicamente
            # es el bloque que se desea leer
            return Evento(TipoEventoProcesador.PR_LEC, operacion)

        bloque, valor = operacion.split("=")
        return Evento(TipoEventoProcesador.PR_ESC, bloque, valor)
