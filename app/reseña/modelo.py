from datetime import datetime


class Reseña:
    """
    Reseña de un usuario sobre un anime.
    Restricción: un usuario solo puede tener una reseña por anime.
    """

    def __init__(self, oid_anime, oid_usuario, nota, comentario):
        """
        Inicializa una reseña.
        :param oid_anime: OID en string del anime reseñado.
        :param oid_usuario: OID en string del usuario autor.
        :param nota: Puntuación del 1 al 10 (int).
        :param comentario: Texto de la reseña.
        """
        self.oid_anime = str(oid_anime)
        self.oid_usuario = str(oid_usuario)
        self.nota = int(nota)
        self.comentario = comentario
        self.fecha = datetime.now()
