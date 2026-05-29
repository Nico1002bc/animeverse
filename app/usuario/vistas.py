import flask
import flask_login
import sirope
import os
import uuid
from .modelo import Usuario

usuario_bp = flask.Blueprint("usuario", __name__, url_prefix="/usuario")
srp = sirope.Sirope()

EXTENSIONES_PERMITIDAS = {"png", "jpg", "jpeg", "gif", "webp"}


def _total_usuarios():
    """Devuelve el número total de usuarios registrados."""
    return sum(1 for _ in srp.load_all(Usuario))


def _extension_valida(nombre):
    """Comprueba si la extensión del archivo es válida."""
    return "." in nombre and nombre.rsplit(".", 1)[1].lower() in EXTENSIONES_PERMITIDAS


@usuario_bp.route("/login", methods=["GET", "POST"])
def login():
    """Muestra el formulario de login y autentica al usuario."""
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for("anime.lista"))

    if flask.request.method == "POST":
        email = flask.request.form.get("email", "").strip()
        password = flask.request.form.get("password", "")
        try:
            usuario = next((u for u in srp.load_all(Usuario) if u.email == email), None)
            if usuario and usuario.check_password(password):
                if not getattr(usuario, "activo", True):
                    flask.flash("Tu cuenta ha sido desactivada. Contacta con un administrador.", "error")
                else:
                    flask_login.login_user(usuario)
                    return flask.redirect(flask.url_for("anime.lista"))
            else:
                flask.flash("Email o contraseña incorrectos.", "error")
        except Exception as ex:
            flask.flash(f"Error de acceso: {ex}", "error")

    return flask.render_template("usuario/login.html")


@usuario_bp.route("/registro", methods=["GET", "POST"])
def registro():
    """Muestra el formulario de registro y crea un nuevo usuario."""
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for("anime.lista"))

    if flask.request.method == "POST":
        email = flask.request.form.get("email", "").strip()
        nick = flask.request.form.get("nick", "").strip()
        password = flask.request.form.get("password", "")
        confirm = flask.request.form.get("confirm", "")

        if not email or not nick or not password:
            flask.flash("Todos los campos son obligatorios.", "error")
        elif password != confirm:
            flask.flash("Las contraseñas no coinciden.", "error")
        else:
            try:
                existente = next((u for u in srp.load_all(Usuario) if u.email == email), None)
                if existente:
                    flask.flash("Ya existe una cuenta con ese email.", "error")
                else:
                    # El primer usuario registrado es administrador
                    rol = "admin" if _total_usuarios() == 0 else "user"
                    nuevo = Usuario(email, password, nick, rol)
                    srp.save(nuevo)
                    flask.flash("Cuenta creada. ¡Ya puedes iniciar sesión!", "success")
                    return flask.redirect(flask.url_for("usuario.login"))
            except Exception as ex:
                flask.flash(f"Error al registrar: {ex}", "error")

    return flask.render_template("usuario/registro.html")


@usuario_bp.route("/perfil")
@flask_login.login_required
def perfil():
    from ..reseña.modelo import Reseña
    from ..anime.modelo import Anime

    from ..watchlist.modelo import EntradaWatchlist

    oid_str = str(flask_login.current_user.__oid__)
    try:
        reseñas = [r for r in srp.load_all(Reseña) if r.oid_usuario == oid_str]
        watchlist = [w for w in srp.load_all(EntradaWatchlist) if w.oid_usuario == oid_str]
        animes = {str(a.__oid__): a for a in srp.load_all(Anime)}
    except Exception:
        reseñas, watchlist, animes = [], [], {}

    return flask.render_template("usuario/perfil.html", reseñas=reseñas, watchlist=watchlist, animes=animes)


@usuario_bp.route("/editar", methods=["GET", "POST"])
@flask_login.login_required
def editar_perfil():
    """Permite al usuario editar su nick, contraseña y foto de perfil."""
    usuario = flask_login.current_user

    if flask.request.method == "POST":
        nick = flask.request.form.get("nick", "").strip()
        password_actual = flask.request.form.get("password_actual", "")
        password_nueva = flask.request.form.get("password_nueva", "")
        password_confirm = flask.request.form.get("password_confirm", "")

        if not nick:
            flask.flash("El nombre de usuario no puede estar vacío.", "error")
            return flask.render_template("usuario/editar.html")

        try:
            # Actualizar nick
            usuario.nick = nick

            # Cambiar contraseña (solo si se rellena)
            if password_nueva:
                if not usuario.check_password(password_actual):
                    flask.flash("La contraseña actual es incorrecta.", "error")
                    return flask.render_template("usuario/editar.html")
                if len(password_nueva) < 6:
                    flask.flash("La nueva contraseña debe tener al menos 6 caracteres.", "error")
                    return flask.render_template("usuario/editar.html")
                if password_nueva != password_confirm:
                    flask.flash("Las nuevas contraseñas no coinciden.", "error")
                    return flask.render_template("usuario/editar.html")
                usuario.cambiar_password(password_nueva)

            # Subir foto de perfil
            foto = flask.request.files.get("foto")
            if foto and foto.filename:
                if not _extension_valida(foto.filename):
                    flask.flash("Formato de imagen no válido. Usa PNG, JPG, GIF o WebP.", "error")
                    return flask.render_template("usuario/editar.html")

                # Borrar foto anterior si existe
                foto_anterior = getattr(usuario, "foto", "")
                if foto_anterior:
                    ruta_anterior = os.path.join(flask.current_app.config["UPLOAD_FOLDER"], foto_anterior)
                    if os.path.exists(ruta_anterior):
                        os.remove(ruta_anterior)

                # Guardar nueva foto con nombre único
                ext = foto.filename.rsplit(".", 1)[1].lower()
                nombre_archivo = f"{uuid.uuid4().hex}.{ext}"
                ruta = os.path.join(flask.current_app.config["UPLOAD_FOLDER"], nombre_archivo)
                foto.save(ruta)
                usuario.foto = nombre_archivo

            # Eliminar foto si se solicita
            if flask.request.form.get("eliminar_foto") == "1":
                foto_actual = getattr(usuario, "foto", "")
                if foto_actual:
                    ruta = os.path.join(flask.current_app.config["UPLOAD_FOLDER"], foto_actual)
                    if os.path.exists(ruta):
                        os.remove(ruta)
                    usuario.foto = ""

            srp.save(usuario)
            flask.flash("Perfil actualizado correctamente.", "success")
            return flask.redirect(flask.url_for("anime.lista"))

        except Exception as ex:
            flask.flash(f"Error al actualizar perfil: {ex}", "error")

    return flask.render_template("usuario/editar.html")


@usuario_bp.route("/logout")
@flask_login.login_required
def logout():
    """Cierra la sesión del usuario actual."""
    flask_login.logout_user()
    return flask.redirect(flask.url_for("usuario.login"))
