import json
import threading

import paho.mqtt.publish as publish

from tipo_peticion import TipoPeticion
from procesador_mensajes import ProcesadorMensajes

HOST = "127.0.0.1"
PORT = 8000
MSI = "msi"


class AdministradorMensajes:
    def __init__(self, inner: ProcesadorMensajes):
        self.__inner = inner

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = json.loads(msg.payload)

        _, tipo_peticion = topic.split('/')
        bloque = payload["bloque"]
        valor = None
        if "valor" in payload:
            valor = payload["valor"]

        origen = payload["origen"]

        destino = None
        if "destino" in payload:
            destino = payload["destino"]

        pro_msg = threading.Thread(
            target=self.__inner.procesar_mensaje,
            args=[tipo_peticion, bloque, origen, destino, valor]
        )
        pro_msg.start()
        client.publish('pong', 'ack', 0)

    @staticmethod
    def publicar_mensaje(peticion, bloque, origen, destino=None, valor=None):
        payload = {
            "bloque": bloque
        }

        if peticion == TipoPeticion.RESPUESTA_BLOQUE_LECTURA.value \
                or peticion == TipoPeticion.RESPUESTA_BLOQUE_EXCLUSIVA.value:
            payload["valor"] = valor
            payload["destino"] = destino

        payload["origen"] = origen

        json_payload = json.dumps(payload)
        publish.single(topic=f"{MSI}/{peticion}", payload=json_payload, hostname=HOST, port=PORT)
