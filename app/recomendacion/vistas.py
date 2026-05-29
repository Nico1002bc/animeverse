import flask
import flask_login
import sirope
from .modelo import Recomendacion
from ..anime.modelo import Anime
from ..usuario.modelo import Usuario

recomendacion_bp = flask.Blueprint("recomendacion", __name__, url_prefix="/recomendacion")
srp = sirope.Sirope()


@recomendacion_bp.route("/recibidas")
@flask_login.login_required
def recibidas():
    oid_usuario = str(flask_login.current_user.__oid__)
    try:
        recs = [r for r in srp.load_all(Recomendacion) if r.oid_destino == oid_usuario]
        recs.sort(key=lambda r: r.fecha, reverse=True)
        oids_animes = {r.oid_anime for r in recs}
        oids_usuarios = {r.oid_origen for r in recs}
        animes = {str(a.__oid__): a for a in srp.load_all(Anime) if str(a.__oid__) in oids_animes}
        usuarios = {str(u.__oid__): u for u in srp.load_all(Usuario) if str(u.__oid__) in oids_usuarios}
    except Exception:
        recs, animes, usuarios = [], {}, {}
        flask.flash("Error al cargar recomendaciones.", "error")

    for r in recs:
        if not r.leida:
            try:
                r.leida = True
                srp.save(r)
            except Exception:
                pass

    return flask.render_template("recomendacion/lista.html",
                                 recs=recs, animes=animes, usuarios=usuarios)


@recomendacion_bp.route("/para-ti")
@flask_login.login_required
def para_ti():
    from ..reseña.modelo import Reseña

    oid_usuario = str(flask_login.current_user.__oid__)
    try:
        animes = list(srp.load_all(Anime))
        reseñas = [r for r in srp.load_all(Reseña) if r.oid_usuario == oid_usuario]
    except Exception:
        animes, reseñas = [], []
        flask.flash("Error al cargar datos.", "error")

    animes_dict = {str(a.__oid__): a for a in animes}
    oids_interactuados = {r.oid_anime for r in reseñas}

    conteo_generos = {}
    for oid in oids_interactuados:
        anime = animes_dict.get(oid)
        if anime:
            for g in (anime.generos or []):
                conteo_generos[g] = conteo_generos.get(g, 0) + 1

    generos_favoritos = sorted(conteo_generos.keys(), key=lambda g: conteo_generos[g], reverse=True)

    todas_reseñas = list(srp.load_all(Reseña))
    notas_por_anime = {}
    for r in todas_reseñas:
        notas_por_anime.setdefault(r.oid_anime, []).append(r.nota)

    sugerencias = []
    for a in animes:
        oid_a = str(a.__oid__)
        if oid_a in oids_interactuados:
            continue
        afinidad = sum(1 for g in generos_favoritos[:5] if g in set(a.generos or []))
        if afinidad > 0:
            notas = notas_por_anime.get(oid_a, [])
            nota_media = round(sum(notas) / len(notas), 1) if notas else None
            sugerencias.append((a, afinidad, nota_media))

    sugerencias.sort(key=lambda x: (x[1], x[2] or 0), reverse=True)
    sugerencias = sugerencias[:10]

    return flask.render_template("recomendacion/para_ti.html",
                                 sugerencias=sugerencias,
                                 generos_favoritos=generos_favoritos[:5],
                                 conteo_generos=conteo_generos)


@recomendacion_bp.route("/buscar-usuario")
@flask_login.login_required
def buscar_usuario():
    q = flask.request.args.get("q", "").strip().lower()
    if len(q) < 2:
        return flask.jsonify([])

    oid_actual = str(flask_login.current_user.__oid__)
    resultados = []
    try:
        for u in srp.load_all(Usuario):
            if str(u.__oid__) == oid_actual:
                continue
            if not getattr(u, "activo", True):
                continue
            if q in u.nick.lower() or q in u.email.lower():
                resultados.append({
                    "oid": str(u.__oid__),
                    "nick": u.nick,
                    "email": u.email,
                    "foto": getattr(u, "foto", "") or ""
                })
                if len(resultados) >= 10:
                    break
    except Exception:
        pass

    return flask.jsonify(resultados)


@recomendacion_bp.route("/enviar", methods=["GET", "POST"])
@flask_login.login_required
def enviar():
    try:
        animes = list(srp.load_all(Anime))
        animes.sort(key=lambda a: a.titulo)
    except Exception:
        animes = []
        flask.flash("Error al cargar animes.", "error")

    if flask.request.method == "POST":
        oid_anime = flask.request.form.get("oid_anime", "")
        oid_destino = flask.request.form.get("oid_destino", "")
        motivo = flask.request.form.get("motivo", "").strip()

        if not oid_anime or not oid_destino or not motivo:
            flask.flash("Todos los campos son obligatorios.", "error")
        else:
            destino = next(
                (u for u in srp.load_all(Usuario) if str(u.__oid__) == oid_destino), None
            )
            if not destino:
                flask.flash("El usuario destinatario no existe.", "error")
            else:
                try:
                    oid_origen = str(flask_login.current_user.__oid__)
                    rec = Recomendacion(oid_anime, oid_origen, oid_destino, motivo)
                    srp.save(rec)
                    flask.flash(f"Recomendación enviada a {destino.nick}.", "success")
                    return flask.redirect(flask.url_for("anime.lista"))
                except Exception as ex:
                    flask.flash(f"Error al enviar: {ex}", "error")

    return flask.render_template("recomendacion/enviar.html", animes=animes)


@recomendacion_bp.route("/<oid>/borrar", methods=["POST"])
@flask_login.login_required
def borrar(oid):
    rec = next((r for r in srp.load_all(Recomendacion) if str(r.__oid__) == oid), None)
    if not rec:
        flask.flash("Recomendación no encontrada.", "error")
        return flask.redirect(flask.url_for("recomendacion.recibidas"))

    if rec.oid_destino != str(flask_login.current_user.__oid__):
        flask.flash("Sin permisos para eliminar esta recomendación.", "error")
        return flask.redirect(flask.url_for("recomendacion.recibidas"))

    try:
        srp.delete(rec.__oid__)
        flask.flash("Recomendación eliminada.", "success")
    except Exception as ex:
        flask.flash(f"Error: {ex}", "error")

    return flask.redirect(flask.url_for("recomendacion.recibidas"))
