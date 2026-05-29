import flask
import flask_login
import sirope
from datetime import datetime
from .modelo import EntradaWatchlist
from ..anime.modelo import Anime

watchlist_bp = flask.Blueprint("watchlist", __name__, url_prefix="/watchlist")
srp = sirope.Sirope()


@watchlist_bp.route("/")
@flask_login.login_required
def lista():
    """Muestra la lista de seguimiento personal del usuario actual."""
    oid_usuario = str(flask_login.current_user.__oid__)
    try:
        entradas = [w for w in srp.load_all(EntradaWatchlist) if w.oid_usuario == oid_usuario]
        animes = {str(a.__oid__): a for a in srp.load_all(Anime)}
    except Exception:
        entradas, animes = [], {}
        flask.flash("Error al cargar la watchlist.", "error")

    # Agrupar por estado
    por_estado = {estado: [] for estado in EntradaWatchlist.ESTADOS}
    for entrada in entradas:
        anime = animes.get(entrada.oid_anime)
        if anime:
            por_estado.setdefault(entrada.estado, []).append((entrada, anime))

    return flask.render_template("watchlist/lista.html",
                                 por_estado=por_estado,
                                 estados=EntradaWatchlist.ESTADOS)


@watchlist_bp.route("/<oid_anime>/añadir", methods=["POST"])
@flask_login.login_required
def anyadir(oid_anime):
    """Añade un anime a la watchlist del usuario con estado inicial."""
    oid_usuario = str(flask_login.current_user.__oid__)
    estado = flask.request.form.get("estado", "planificado")

    ya_existe = next(
        (w for w in srp.load_all(EntradaWatchlist)
         if w.oid_anime == oid_anime and w.oid_usuario == oid_usuario),
        None
    )
    if ya_existe:
        flask.flash("Este anime ya está en tu watchlist.", "warning")
    else:
        try:
            if estado not in EntradaWatchlist.ESTADOS:
                estado = "planificado"
            entrada = EntradaWatchlist(oid_anime, oid_usuario, estado)
            srp.save(entrada)
            flask.flash("Añadido a tu watchlist.", "success")
        except Exception as ex:
            flask.flash(f"Error: {ex}", "error")

    return flask.redirect(flask.url_for("anime.detalle", oid=oid_anime))


@watchlist_bp.route("/<oid>/estado", methods=["POST"])
@flask_login.login_required
def cambiar_estado(oid):
    """Actualiza el estado de seguimiento de una entrada de watchlist."""
    entrada = next((w for w in srp.load_all(EntradaWatchlist) if str(w.__oid__) == oid), None)
    if not entrada:
        flask.flash("Entrada no encontrada.", "error")
        return flask.redirect(flask.url_for("watchlist.lista"))

    if entrada.oid_usuario != str(flask_login.current_user.__oid__):
        flask.flash("No puedes modificar la watchlist de otro usuario.", "error")
        return flask.redirect(flask.url_for("watchlist.lista"))

    nuevo_estado = flask.request.form.get("estado", "")
    if nuevo_estado not in EntradaWatchlist.ESTADOS:
        flask.flash("Estado no válido.", "error")
    else:
        try:
            entrada.estado = nuevo_estado
            if nuevo_estado == "completado":
                entrada.fecha_fin = datetime.now()
            else:
                entrada.fecha_fin = None
            srp.save(entrada)
            flask.flash("Estado actualizado.", "success")
        except Exception as ex:
            flask.flash(f"Error: {ex}", "error")

    return flask.redirect(flask.url_for("watchlist.lista"))


@watchlist_bp.route("/<oid>/progreso", methods=["POST"])
@flask_login.login_required
def progreso(oid):
    """Actualiza el episodio actual de una entrada de watchlist."""
    entrada = next((w for w in srp.load_all(EntradaWatchlist) if str(w.__oid__) == oid), None)
    if not entrada:
        flask.flash("Entrada no encontrada.", "error")
        return flask.redirect(flask.url_for("watchlist.lista"))

    if entrada.oid_usuario != str(flask_login.current_user.__oid__):
        flask.flash("Sin permisos.", "error")
        return flask.redirect(flask.url_for("watchlist.lista"))

    try:
        ep = flask.request.form.get("episodio_actual", "0").strip()
        entrada.episodio_actual = int(ep) if ep.isdigit() else 0
        srp.save(entrada)
    except Exception as ex:
        flask.flash(f"Error: {ex}", "error")

    return flask.redirect(flask.url_for("watchlist.lista"))


@watchlist_bp.route("/<oid>/borrar", methods=["POST"])
@flask_login.login_required
def borrar(oid):
    """Elimina una entrada de la watchlist del usuario."""
    entrada = next((w for w in srp.load_all(EntradaWatchlist) if str(w.__oid__) == oid), None)
    if not entrada:
        flask.flash("Entrada no encontrada.", "error")
        return flask.redirect(flask.url_for("watchlist.lista"))

    if entrada.oid_usuario != str(flask_login.current_user.__oid__):
        flask.flash("Sin permisos.", "error")
        return flask.redirect(flask.url_for("watchlist.lista"))

    try:
        srp.delete(entrada.__oid__)
        flask.flash("Eliminado de tu watchlist.", "success")
    except Exception as ex:
        flask.flash(f"Error: {ex}", "error")

    return flask.redirect(flask.url_for("watchlist.lista"))
