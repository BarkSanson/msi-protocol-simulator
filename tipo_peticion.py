from enum import Enum


class TipoPeticion(Enum):
    PETICION_LECTURA = "ptlec"
    PETICION_LECTURA_EXCLUSIVA = "ptlecex"
    RESPUESTA_BLOQUE_LECTURA = "rpbloquelec"
    RESPUESTA_BLOQUE_EXCLUSIVA = "rpbloqueex"
