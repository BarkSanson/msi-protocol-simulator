import json

import paho.mqtt.publish as publish

from tipo_peticion import TipoPeticion

HOST = "127.0.0.1"
MSI = "msi"


class AdministradorMensajes:
    @staticmethod
    def publicar_mensaje(peticion, bloque, origen, valor=None):
        payload = {
            "bloque": bloque
        }

        if peticion == TipoPeticion.RESPUESTA_BLOQUE_LECTURA \
                or peticion == TipoPeticion.RESPUESTA_BLOQUE_EXCLUSIVA:
            payload["valor"] = valor

        payload["origen"] = origen

        json_payload = json.dumps(payload)
        publish.single(topic=f"{MSI}/{peticion}", payload=json_payload, hostname=HOST)
