import flask
import flask_login
import sirope
from .modelo import Reseña
from ..anime.modelo import Anime

reseña_bp = flask.Blueprint("reseña", __name__, url_prefix="/reseña")
srp = sirope.Sirope()


@reseña_bp.route("/<oid_anime>/crear", methods=["GET", "POST"])
@flask_login.login_required
def crear(oid_anime):
    """
    Crea una reseña para un anime. Un usuario solo puede reseñar
    un anime una vez; si ya existe, se redirige a la edición.
    """
    anime = next((a for a in srp.load_all(Anime) if str(a.__oid__) == oid_anime), None)
    if not anime:
        flask.flash("El anime no existe.", "error")
        return flask.redirect(flask.url_for("anime.lista"))

    oid_usuario = str(flask_login.current_user.__oid__)
    existente = next(
        (r for r in srp.load_all(Reseña)
         if r.oid_anime == oid_anime and r.oid_usuario == oid_usuario),
        None
    )
    if existente:
        flask.flash("Ya tienes una reseña para este anime. Puedes editarla.", "warning")
        return flask.redirect(flask.url_for("anime.detalle", oid=oid_anime))

    if flask.request.method == "POST":
        nota_str = flask.request.form.get("nota", "")
        comentario = flask.request.form.get("comentario", "").strip()
        if not nota_str.isdigit() or not (1 <= int(nota_str) <= 5):
            flask.flash("La nota debe ser un número entre 1 y 5.", "error")
        elif not comentario:
            flask.flash("El comentario no puede estar vacío.", "error")
        else:
            try:
                reseña = Reseña(oid_anime, oid_usuario, int(nota_str), comentario)
                srp.save(reseña)
                flask.flash("Reseña publicada correctamente.", "success")
                return flask.redirect(flask.url_for("anime.detalle", oid=oid_anime))
            except Exception as ex:
                flask.flash(f"Error al guardar la reseña: {ex}", "error")

    return flask.render_template("reseña/crear.html", anime=anime, oid_anime=oid_anime)


@reseña_bp.route("/<oid>/editar", methods=["GET", "POST"])
@flask_login.login_required
def editar(oid):
    """
    Edita una reseña existente. Solo el autor puede editarla.
    """
    reseña = next((r for r in srp.load_all(Reseña) if str(r.__oid__) == oid), None)
    if not reseña:
        flask.flash("La reseña no existe.", "error")
        return flask.redirect(flask.url_for("anime.lista"))

    if reseña.oid_usuario != str(flask_login.current_user.__oid__):
        flask.flash("Solo puedes editar tus propias reseñas.", "error")
        return flask.redirect(flask.url_for("anime.detalle", oid=reseña.oid_anime))

    anime = next((a for a in srp.load_all(Anime) if str(a.__oid__) == reseña.oid_anime), None)

    if flask.request.method == "POST":
        nota_str = flask.request.form.get("nota", "")
        comentario = flask.request.form.get("comentario", "").strip()
        if not nota_str.isdigit() or not (1 <= int(nota_str) <= 5):
            flask.flash("La nota debe ser entre 1 y 5.", "error")
        elif not comentario:
            flask.flash("El comentario no puede estar vacío.", "error")
        else:
            try:
                reseña.nota = int(nota_str)
                reseña.comentario = comentario
                srp.save(reseña)
                flask.flash("Reseña actualizada.", "success")
                return flask.redirect(flask.url_for("anime.detalle", oid=reseña.oid_anime))
            except Exception as ex:
                flask.flash(f"Error al actualizar: {ex}", "error")

    return flask.render_template("reseña/editar.html", reseña=reseña, anime=anime, oid=oid)


@reseña_bp.route("/<oid>/borrar", methods=["POST"])
@flask_login.login_required
def borrar(oid):
    """
    Elimina una reseña. Solo el autor o un administrador pueden hacerlo.
    """
    reseña = next((r for r in srp.load_all(Reseña) if str(r.__oid__) == oid), None)
    if not reseña:
        flask.flash("La reseña no existe.", "error")
        return flask.redirect(flask.url_for("anime.lista"))

    es_autor = reseña.oid_usuario == str(flask_login.current_user.__oid__)
    if not es_autor and not flask_login.current_user.es_admin:
        flask.flash("Sin permisos para eliminar esta reseña.", "error")
        return flask.redirect(flask.url_for("anime.detalle", oid=reseña.oid_anime))

    oid_anime = reseña.oid_anime
    try:
        srp.delete(reseña.__oid__)
        flask.flash("Reseña eliminada.", "success")
    except Exception as ex:
        flask.flash(f"Error al eliminar: {ex}", "error")

    return flask.redirect(flask.url_for("anime.detalle", oid=oid_anime))
