import json
import threading

import paho.mqtt.publish as publish

from tipo_peticion import TipoPeticion
from procesador_mensajes import ProcesadorMensajes

HOST = "127.0.0.1"
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

        pro_msg = threading.Thread(target=self.__inner.procesar_mensaje, args=[tipo_peticion, bloque, origen, valor])
        pro_msg.start()
        client.publish('pong', 'ack', 0)

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
