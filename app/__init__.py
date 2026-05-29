import os
import flask
import flask_login
import sirope


def create_app():
    app = flask.Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "aniverse-dev-key")
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    login_manager = flask_login.LoginManager(app)
    login_manager.login_view = "usuario.login"
    login_manager.login_message = "Inicia sesión para continuar."
    login_manager.login_message_category = "warning"

    app.sirope = sirope.Sirope()

    @login_manager.user_loader
    def load_user(user_id):
        from app.usuario.modelo import Usuario
        return next((u for u in flask.current_app.sirope.load_all(Usuario) if str(u.__oid__) == user_id), None)

    @app.context_processor
    def inject_notif_count():
        if not flask_login.current_user.is_authenticated:
            return {"notif_count": 0}
        try:
            from app.recomendacion.modelo import Recomendacion
            oid = str(flask_login.current_user.__oid__)
            count = sum(1 for r in flask.current_app.sirope.load_all(Recomendacion)
                        if r.oid_destino == oid and not r.leida)
        except Exception:
            count = 0
        return {"notif_count": count}

    from app.usuario.vistas import usuario_bp
    from app.anime.vistas import anime_bp
    from app.reseña.vistas import reseña_bp
    from app.recomendacion.vistas import recomendacion_bp
    from app.watchlist.vistas import watchlist_bp

    app.register_blueprint(usuario_bp)
    app.register_blueprint(anime_bp)
    app.register_blueprint(reseña_bp)
    app.register_blueprint(recomendacion_bp)
    app.register_blueprint(watchlist_bp)

    @app.route("/")
    def index():
        return flask.redirect(flask.url_for("anime.lista"))

    return app
