from datetime import datetime


class EntradaWatchlist:
    """
    Entrada en la lista de seguimiento personal de un usuario.
    Registra el estado de visionado de un anime concreto.
    """

    ESTADOS = {
        "planificado": "Planificado",
        "viendo": "Viendo",
        "completado": "Completado",
        "en_espera": "En espera",
        "abandonado": "Abandonado",
    }

    def __init__(self, oid_anime, oid_usuario, estado="planificado"):
        self.oid_anime = str(oid_anime)
        self.oid_usuario = str(oid_usuario)
        self.estado = estado
        self.fecha_inicio = datetime.now()
        self.episodio_actual = 0
        self.fecha_fin = None

    def estado_display(self):
        """Devuelve el texto legible del estado actual."""
        return self.ESTADOS.get(self.estado, self.estado)
