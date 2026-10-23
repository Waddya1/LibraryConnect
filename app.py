"""LibraryConnect entry point. Run with:  flask --app app run --debug"""
from pathlib import Path

from flask import Flask, g, redirect, render_template, request, url_for

import auth
import books
import config
import csrf
import db


def create_app(test_config=None):
    app = Flask(__name__, instance_path=str(config.INSTANCE_DIR))
    app.config.from_object(config.Config)
    if test_config:
        app.config.update(test_config)
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = config.load_secret_key()

    Path(app.instance_path).mkdir(exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(books.bp)

    @app.route("/")
    def index():
        if g.patron is None:
            return redirect(url_for("auth.login"))
        return redirect(url_for("books.list_books"))

    @app.errorhandler(400)
    def bad_request(error):
        return render_template("error.html", code=400,
                               message="Bad request. Please go back and try again."), 400

    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", code=404,
                               message="That page was not found."), 404

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = \
            "default-src 'self'; frame-ancestors 'none'"
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store"
        return response

    return app


app = create_app()
