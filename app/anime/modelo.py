class Anime:
    """
    Entidad principal del catálogo de AniVerse.
    Representa un anime con sus metadatos, géneros y estado de emisión.
    Solo los administradores pueden crear, editar o eliminar animes.
    """

    ESTADOS = {
        "en_emision": "En emisión",
        "finalizado": "Finalizado",
        "proximamente": "Próximamente",
    }

    TIPOS = {
        "serie": "Serie",
        "pelicula": "Película",
        "ova": "OVA",
        "especial": "Especial",
    }

    GENEROS_DISPONIBLES = [
        "Acción", "Aventura", "Comedia", "Drama", "Fantasía",
        "Horror", "Misterio", "Romance", "Sci-Fi", "Slice of Life",
        "Deportes", "Sobrenatural", "Thriller", "Mecha", "Histórico",
    ]

    def __init__(self, titulo, sinopsis, generos, episodios, año, estado, imagen_url="",
                 tipo="serie", trailer_url="", estudio_oid=""):
        self.titulo = titulo
        self.sinopsis = sinopsis
        self.generos = generos if isinstance(generos, list) else [generos]
        self.episodios = episodios
        self.año = año
        self.estado = estado
        self.imagen_url = imagen_url
        self.tipo = tipo
        self.trailer_url = trailer_url
        self.estudio_oid = estudio_oid

    def estado_display(self):
        return self.ESTADOS.get(self.estado, self.estado)

    def tipo_display(self):
        return self.TIPOS.get(getattr(self, "tipo", "serie"), "Serie")

    def puntuacion_media(self, reseñas):
        """
        Calcula la puntuación media de un anime a partir de una lista de reseñas.
        :param reseñas: Lista de objetos Reseña.
        :return: Puntuación media (float) o None si no hay reseñas.
        """
        if not reseñas:
            return None
        notas = [r.nota for r in reseñas if r.oid_anime == str(self.__oid__)]
        return round(sum(notas) / len(notas), 1) if notas else None

    @property
    def generos_str(self):
        """
        Devuelve los géneros como una cadena legible.
        """
        return ", ".join(self.generos) if self.generos else "N/A"

    @property
    def estado_str(self):
        """
        Devuelve el estado como una cadena legible.
        """
        return self.ESTADOS.get(self.estado, self.estado.replace("_", " ").capitalize())

    @property
    def tipo_str(self):
        """
        Devuelve el tipo como una cadena legible.
        """
        return self.TIPOS.get(self.tipo, self.tipo.capitalize())
