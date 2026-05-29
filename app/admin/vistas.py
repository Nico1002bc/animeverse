import flask
import flask_login
import sirope
import functools
from ..usuario.modelo import Usuario
from ..anime.modelo import Anime
from ..reseña.modelo import Reseña
from ..watchlist.modelo import EntradaWatchlist
from ..recomendacion.modelo import Recomendacion

admin_bp = flask.Blueprint("admin", __name__, url_prefix="/admin")
srp = sirope.Sirope()


def admin_required(f):
    """Decorador que restringe el acceso a administradores."""
    @functools.wraps(f)
    @flask_login.login_required
    def decorated(*args, **kwargs):
        if not flask_login.current_user.es_admin:
            flask.flash("Acceso restringido a administradores.", "error")
            return flask.redirect(flask.url_for("anime.lista"))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/")
@admin_required
def dashboard():
    """Panel de administración con estadísticas globales."""
    try:
        animes = list(srp.load_all(Anime))
        usuarios = list(srp.load_all(Usuario))
        reseñas = list(srp.load_all(Reseña))
        watchlists = list(srp.load_all(EntradaWatchlist))
        recomendaciones = list(srp.load_all(Recomendacion))
    except Exception:
        animes, usuarios, reseñas, watchlists, recomendaciones = [], [], [], [], []
        flask.flash("Error al cargar estadísticas.", "error")

    # Últimos 5 animes (por título como fallback, ya que no hay fecha de creación)
    ultimos_animes = sorted(animes, key=lambda a: a.titulo)[:5]

    # Usuarios más activos (por número de reseñas)
    reseñas_por_usuario = {}
    for r in reseñas:
        reseñas_por_usuario[r.oid_usuario] = reseñas_por_usuario.get(r.oid_usuario, 0) + 1
    usuarios_dict = {str(u.__oid__): u for u in usuarios}
    top_usuarios = sorted(reseñas_por_usuario.items(), key=lambda x: x[1], reverse=True)[:5]
    top_usuarios_info = [
        (usuarios_dict.get(oid, None), count)
        for oid, count in top_usuarios
        if usuarios_dict.get(oid)
    ]

    # Nota media global
    notas = [r.nota for r in reseñas]
    nota_media = round(sum(notas) / len(notas), 1) if notas else None

    stats = {
        "total_animes": len(animes),
        "total_usuarios": len(usuarios),
        "total_reseñas": len(reseñas),
        "total_watchlists": len(watchlists),
        "total_recomendaciones": len(recomendaciones),
        "nota_media": nota_media,
    }

    return flask.render_template("admin/dashboard.html",
                                 stats=stats,
                                 ultimos_animes=ultimos_animes,
                                 top_usuarios=top_usuarios_info)


@admin_bp.route("/usuarios")
@admin_required
def usuarios():
    """Lista todos los usuarios para gestión administrativa."""
    try:
        todos = list(srp.load_all(Usuario))
        todos.sort(key=lambda u: u.nick.lower())
    except Exception:
        todos = []
        flask.flash("Error al cargar usuarios.", "error")

    # Contar reseñas por usuario
    try:
        reseñas = list(srp.load_all(Reseña))
        reseñas_count = {}
        for r in reseñas:
            reseñas_count[r.oid_usuario] = reseñas_count.get(r.oid_usuario, 0) + 1
    except Exception:
        reseñas_count = {}

    return flask.render_template("admin/usuarios.html",
                                 usuarios=todos,
                                 reseñas_count=reseñas_count)


@admin_bp.route("/usuarios/<oid>/toggle-activo", methods=["POST"])
@admin_required
def toggle_activo(oid):
    """
    Activa o desactiva la cuenta de un usuario.
    """
    usuario = next((u for u in srp.load_all(Usuario) if str(u.__oid__) == oid), None)
    if not usuario:
        flask.flash("Usuario no encontrado.", "error")
        return flask.redirect(flask.url_for("admin.usuarios"))

    # No permitir desactivarse a sí mismo
    if str(flask_login.current_user.__oid__) == oid:
        flask.flash("No puedes desactivar tu propia cuenta.", "error")
        return flask.redirect(flask.url_for("admin.usuarios"))

    try:
        # Compatibilidad: si no tiene atributo 'activo', lo inicializamos
        estado_actual = getattr(usuario, "activo", True)
        usuario.activo = not estado_actual
        srp.save(usuario)
        if usuario.activo:
            flask.flash(f"Cuenta de '{usuario.nick}' activada.", "success")
        else:
            flask.flash(f"Cuenta de '{usuario.nick}' desactivada.", "warning")
    except Exception as ex:
        flask.flash(f"Error al cambiar estado: {ex}", "error")

    return flask.redirect(flask.url_for("admin.usuarios"))


@admin_bp.route("/usuarios/<oid>/borrar", methods=["POST"])
@admin_required
def borrar_usuario(oid):
    """
    Elimina un usuario y todos sus datos relacionados.
    Integridad referencial: borra reseñas, watchlist y recomendaciones.
    """
    usuario = next((u for u in srp.load_all(Usuario) if str(u.__oid__) == oid), None)
    if not usuario:
        flask.flash("Usuario no encontrado.", "error")
        return flask.redirect(flask.url_for("admin.usuarios"))

    # No permitir eliminarse a sí mismo
    if str(flask_login.current_user.__oid__) == oid:
        flask.flash("No puedes eliminar tu propia cuenta.", "error")
        return flask.redirect(flask.url_for("admin.usuarios"))

    try:
        nick = usuario.nick
        # Eliminar reseñas del usuario
        for r in list(srp.load_all(Reseña)):
            if r.oid_usuario == oid:
                srp.delete(r.__oid__)
        # Eliminar watchlist del usuario
        for w in list(srp.load_all(EntradaWatchlist)):
            if w.oid_usuario == oid:
                srp.delete(w.__oid__)
        # Eliminar recomendaciones enviadas y recibidas
        for rec in list(srp.load_all(Recomendacion)):
            if rec.oid_origen == oid or rec.oid_destino == oid:
                srp.delete(rec.__oid__)
        # Eliminar el usuario
        srp.delete(usuario.__oid__)
        flask.flash(f"Usuario '{nick}' y todos sus datos eliminados.", "success")
    except Exception as ex:
        flask.flash(f"Error al eliminar usuario: {ex}", "error")

    return flask.redirect(flask.url_for("admin.usuarios"))
