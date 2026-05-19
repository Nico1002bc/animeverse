from datetime import datetime


class Recomendacion:
    """
    Recomendación de un anime enviada de un usuario a otro.
    Permite compartir series con un motivo personalizado.
    """

    def __init__(self, oid_anime, oid_origen, oid_destino, motivo):
        """
        Inicializa una recomendación.
        :param oid_anime: OID en string del anime recomendado.
        :param oid_origen: OID en string del usuario que recomienda.
        :param oid_destino: OID en string del usuario destinatario.
        :param motivo: Texto explicando la recomendación.
        """
        self.oid_anime = str(oid_anime)
        self.oid_origen = str(oid_origen)
        self.oid_destino = str(oid_destino)
        self.motivo = motivo
        self.fecha = datetime.now()
        self.leida = False
