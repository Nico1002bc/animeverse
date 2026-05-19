import flask_login
import hashlib


class Usuario(flask_login.UserMixin):
    """
    Modelo de usuario de AniVerse.
    Almacena email, nick visible, contraseña hasheada y rol (admin|user).
    El primer usuario registrado en el sistema se convierte en admin.
    """

    def __init__(self, email, password, nick, rol="user"):
        """
        Inicializa un nuevo usuario.
        :param email: Email único, usado como credencial de acceso.
        :param password: Contraseña en texto plano (se almacena como SHA-256).
        :param nick: Nombre visible en la aplicación.
        :param rol: 'admin' o 'user'. Por defecto 'user'.
        """
        self.email = email
        self._password = hashlib.sha256(password.encode()).hexdigest()
        self.nick = nick
        self.rol = rol
        self.activo = True
        self.foto = ""

    @property
    def id(self):
        """Identificador único asignado por Sirope."""
        return self.__oid__

    @property
    def is_active(self):
        """Flask-Login: permite el login solo si la cuenta está activa."""
        return getattr(self, "activo", True)

    @property
    def es_admin(self):
        """Devuelve True si el usuario tiene privilegios de administrador."""
        return self.rol == "admin"

    def check_password(self, password):
        """
        Verifica si la contraseña proporcionada coincide con la almacenada.
        :param password: Contraseña en texto plano a comprobar.
        :return: True si es correcta, False en caso contrario.
        """
        hashed = hashlib.sha256(password.encode()).hexdigest()
        return self._password == hashed

    def cambiar_password(self, nueva):
        """
        Actualiza la contraseña del usuario.
        :param nueva: Nueva contraseña en texto plano.
        """
        self._password = hashlib.sha256(nueva.encode()).hexdigest()

    @property
    def tiene_foto(self):
        """Devuelve True si el usuario tiene foto de perfil."""
        return bool(getattr(self, "foto", ""))

    @property
    def iniciales(self):
        """Devuelve las iniciales del nick para el avatar por defecto."""
        return self.nick[0].upper() if self.nick else "?"
