from datetime import datetime, timezone


class EventosFileWriter:

    @staticmethod
    def escribir_evento(fichero: str, evento: str, bloque: str, valor: str):
        with open(fichero, "a") as file:
            hora = datetime.now(timezone.utc)

            file.write(f"{hora} {evento} Bloque {bloque} con valor {valor}\n")
