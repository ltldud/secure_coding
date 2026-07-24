import os
import logging

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template
from flask_login import current_user

from config import DevConfig, ProdConfig
from extensions import db, login_manager, csrf, socketio, limiter


def create_app():
    app = Flask(__name__)
    env = os.environ.get("FLASK_ENV", "development")
    app.config.from_object(ProdConfig if env == "production" else DevConfig)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        user = db.session.get(User, user_id)
        if user is not None and user.status == "suspended":
            return None
        return user

    from blueprints.auth import auth_bp
    from blueprints.profile import profile_bp
    from blueprints.products import products_bp
    from blueprints.reports import reports_bp
    from blueprints.transfers import transfers_bp
    from blueprints.admin import admin_bp
    from blueprints.chat import chat_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(transfers_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(chat_bp)

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            from flask import redirect, url_for
            return redirect(url_for("products.dashboard"))
        return render_template("index.html")

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self' ws: wss:;"
        )
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403, message="접근 권한이 없습니다."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="페이지를 찾을 수 없습니다."), 404

    @app.errorhandler(429)
    def rate_limited(e):
        return render_template("error.html", code=429, message="요청이 너무 잦습니다. 잠시 후 다시 시도하세요."), 429

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Unhandled server error")
        return render_template("error.html", code=500, message="서버 오류가 발생했습니다."), 500

    if not app.debug:
        logging.basicConfig(level=logging.INFO)

    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=app.config["DEBUG"],
        allow_unsafe_werkzeug=True,
    )
