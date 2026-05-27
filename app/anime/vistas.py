import flask
import flask_login
import sirope
from .modelo import Anime
from ..reseña.modelo import Reseña

anime_bp = flask.Blueprint("anime", __name__, url_prefix="/anime")
srp = sirope.Sirope()


def _buscar_anime(oid_str):
    return next((a for a in srp.load_all(Anime) if str(a.__oid__) == oid_str), None)


@anime_bp.route("/")
@flask_login.login_required
def lista():
    q = flask.request.args.get("q", "").lower()
    genero = flask.request.args.get("genero", "")
    orden = flask.request.args.get("orden", "titulo")
    try:
        pagina = max(1, int(flask.request.args.get("pagina", "1")))
    except (ValueError, TypeError):
        pagina = 1
    POR_PAGINA = 10

    try:
        todos = list(srp.load_all(Anime))
        reseñas = list(srp.load_all(Reseña))
    except Exception:
        todos, reseñas = [], []
        flask.flash("Error al cargar el catálogo.", "error")

    if q:
        todos = [a for a in todos if q in a.titulo.lower()]
    if genero:
        todos = [a for a in todos if genero in (a.generos or [])]

    notas_por_anime = {}
    for r in reseñas:
        notas_por_anime.setdefault(r.oid_anime, []).append(r.nota)
    for a in todos:
        notas = notas_por_anime.get(str(a.__oid__), [])
        a._nota_media = round(sum(notas) / len(notas), 1) if notas else None

    if orden == "año_desc":
        todos.sort(key=lambda a: a.año, reverse=True)
    elif orden == "año_asc":
        todos.sort(key=lambda a: a.año)
    else:
        todos.sort(key=lambda a: a.titulo.lower())

    total = len(todos)
    total_paginas = max(1, (total + POR_PAGINA - 1) // POR_PAGINA)
    pagina = min(pagina, total_paginas)
    inicio = (pagina - 1) * POR_PAGINA
    animes_pagina = todos[inicio:inicio + POR_PAGINA]

    return flask.render_template("anime/lista.html",
                                 animes=animes_pagina,
                                 busqueda=q,
                                 genero_sel=genero,
                                 orden_sel=orden,
                                 generos=Anime.GENEROS_DISPONIBLES,
                                 pagina=pagina,
                                 total_paginas=total_paginas)


@anime_bp.route("/<oid>")
@flask_login.login_required
def detalle(oid):
    anime = _buscar_anime(oid)
    if not anime:
        flask.flash("El anime solicitado no existe.", "error")
        return flask.redirect(flask.url_for("anime.lista"))

    from ..usuario.modelo import Usuario
    try:
        reseñas = [r for r in srp.load_all(Reseña) if r.oid_anime == oid]
        usuarios = {str(u.__oid__): u for u in srp.load_all(Usuario)}
    except Exception:
        reseñas, usuarios = [], {}

    ya_reseno = any(r.oid_usuario == str(flask_login.current_user.__oid__) for r in reseñas)

    return flask.render_template("anime/detalle.html",
                                 anime=anime, oid=oid,
                                 reseñas=reseñas,
                                 usuarios=usuarios,
                                 puntuacion=anime.puntuacion_media(reseñas),
                                 ya_reseno=ya_reseno)


@anime_bp.route("/crear", methods=["GET", "POST"])
@flask_login.login_required
def crear():
    if not flask_login.current_user.es_admin:
        flask.flash("Solo los administradores pueden añadir animes.", "error")
        return flask.redirect(flask.url_for("anime.lista"))

    if flask.request.method == "POST":
        titulo = flask.request.form.get("titulo", "").strip()
        sinopsis = flask.request.form.get("sinopsis", "").strip()
        generos = flask.request.form.getlist("generos")
        ep = flask.request.form.get("episodios", "").strip()
        año = flask.request.form.get("año", "").strip()
        estado = flask.request.form.get("estado", "finalizado")
        imagen_url = flask.request.form.get("imagen_url", "").strip()
        tipo = flask.request.form.get("tipo", "serie")
        trailer_url = flask.request.form.get("trailer_url", "").strip()

        errores = []
        if not titulo:
            errores.append("El título es obligatorio.")
        if not sinopsis:
            errores.append("La sinopsis es obligatoria.")
        if not año or not año.isdigit():
            errores.append("El año debe ser un número válido.")

        if errores:
            for e in errores:
                flask.flash(e, "error")
            return flask.render_template("anime/crear.html",
                                         generos=Anime.GENEROS_DISPONIBLES,
                                         estados=Anime.ESTADOS,
                                         tipos=Anime.TIPOS,
                                         form=flask.request.form)
        try:
            episodios_int = int(ep) if ep and ep.isdigit() else None
            nuevo = Anime(titulo, sinopsis, generos, episodios_int, int(año), estado,
                          imagen_url, tipo, trailer_url, "")
            srp.save(nuevo)
            flask.flash(f"'{titulo}' añadido al catálogo.", "success")
            return flask.redirect(flask.url_for("anime.lista"))
        except Exception as ex:
            flask.flash(f"Error al guardar: {ex}", "error")

    return flask.render_template("anime/crear.html",
                                 generos=Anime.GENEROS_DISPONIBLES,
                                 estados=Anime.ESTADOS,
                                 tipos=Anime.TIPOS,
                                 form={})


@anime_bp.route("/<oid>/editar", methods=["GET", "POST"])
@flask_login.login_required
def editar(oid):
    if not flask_login.current_user.es_admin:
        flask.flash("Sin permisos de edición.", "error")
        return flask.redirect(flask.url_for("anime.detalle", oid=oid))

    anime = _buscar_anime(oid)
    if not anime:
        flask.flash("El anime no existe.", "error")
        return flask.redirect(flask.url_for("anime.lista"))

    if flask.request.method == "POST":
        titulo = flask.request.form.get("titulo", "").strip()
        if not titulo:
            flask.flash("El título no puede estar vacío.", "error")
            return flask.render_template("anime/editar.html", anime=anime, oid=oid,
                                         generos=Anime.GENEROS_DISPONIBLES, estados=Anime.ESTADOS,
                                         tipos=Anime.TIPOS)
        try:
            anime.titulo = titulo
            anime.sinopsis = flask.request.form.get("sinopsis", "").strip()
            anime.generos = flask.request.form.getlist("generos")
            ep = flask.request.form.get("episodios", "").strip()
            anime.episodios = int(ep) if ep and ep.isdigit() else None
            año = flask.request.form.get("año", str(anime.año)).strip()
            anime.año = int(año) if año.isdigit() else anime.año
            anime.estado = flask.request.form.get("estado", anime.estado)
            anime.imagen_url = flask.request.form.get("imagen_url", "").strip()
            anime.tipo = flask.request.form.get("tipo", getattr(anime, "tipo", "serie"))
            anime.trailer_url = flask.request.form.get("trailer_url", "").strip()
            srp.save(anime)
            flask.flash("Anime actualizado correctamente.", "success")
            return flask.redirect(flask.url_for("anime.detalle", oid=oid))
        except Exception as ex:
            flask.flash(f"Error al actualizar: {ex}", "error")

    return flask.render_template("anime/editar.html", anime=anime, oid=oid,
                                 generos=Anime.GENEROS_DISPONIBLES,
                                 estados=Anime.ESTADOS,
                                 tipos=Anime.TIPOS)


@anime_bp.route("/<oid>/borrar", methods=["POST"])
@flask_login.login_required
def borrar(oid):
    if not flask_login.current_user.es_admin:
        flask.flash("Sin permisos para eliminar animes.", "error")
        return flask.redirect(flask.url_for("anime.lista"))

    anime = _buscar_anime(oid)
    if not anime:
        flask.flash("El anime no existe.", "error")
        return flask.redirect(flask.url_for("anime.lista"))

    try:
        titulo = anime.titulo
        srp.delete(anime.__oid__)
        flask.flash(f"'{titulo}' eliminado.", "success")
    except Exception as ex:
        flask.flash(f"Error al eliminar: {ex}", "error")

    return flask.redirect(flask.url_for("anime.lista"))
