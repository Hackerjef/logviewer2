from __future__ import annotations

from types import FrameType

import logging
import os
import signal

from flask import Flask, render_template, Response, g
from flask_discord import DiscordOAuth2Session

from werkzeug.middleware.proxy_fix import ProxyFix

from logviewer2.utils import DOWNLOAD_FONTS, GET_SECRET_KEY
from logviewer2.utils.decos import with_logs_evidence, with_logs, with_user
from logviewer2.utils.db import DB
from logviewer2.utils.regexcfg import GET_DCONFIG
from logviewer2.views import Auth, Fproxy

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.wsgi_app = ProxyFix(app.wsgi_app)
app.config.from_object(__name__)
app.config.update(
    SECRET_KEY=GET_SECRET_KEY(os.environ),
    MAX_CONTENT_LENGTH=(16 * 1024 * 1024),
    FDIR=DOWNLOAD_FONTS(),
    ISSHUTDOWN=False,
    SHUTDOWNC=0
)

gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)


def keyboard_interrupt_handler(_s: int, _frame: FrameType | None) -> None:
    if not app.config['ISSHUTDOWN']:
        app.config['ISSHUTDOWN'] = True
        if app.config.get("FDIR", False):
            print("~~~cleaning up Fonts~~~")
            app.config["FDIR"].cleanup()
            app.config['SHUTDOWNC'] = +1
        os.kill(os.getpid(), signal.SIGTERM)
    else:
        if app.config['SHUTDOWNC'] >= 10:
            print("kill hit 10 times, shutting down - {}/10".format(app.config['SHUTDOWNC']))
            os.kill(os.getpid(), signal.SIGKILL)
        else:
            app.config['SHUTDOWNC'] = +1
            print("kill hit {}/10 times - killing".format(app.config['SHUTDOWNC']))


signal.signal(signal.SIGINT, keyboard_interrupt_handler)

app.db = DB()
# Auth :)
dconfig = GET_DCONFIG(os.environ)
DiscordOAuth2Session(app, client_id=dconfig["CLIENT_ID"], client_secret=dconfig["CLIENT_SECRET"],
                     redirect_uri=dconfig["CLIENT_REDIRECT_URI"])
app.register_blueprint(Auth)
app.register_blueprint(Fproxy)


# errors
@app.errorhandler(403)
@with_user
def page_not_found(_e):
    return render_template("unauthorized.html", user=g.user), 403


@app.errorhandler(404)
@with_user
def page_not_found(_e):
    return render_template("not_found.html", user=g.user), 404


@app.errorhandler(405)
@with_user
def page_not_found_method(_e):
    return render_template("not_found.html", user=g.user), 405


@app.errorhandler(500)
@with_user
def page_not_found(_e):
    return render_template("server_error.html", user=g.user), 500


# Pages
@app.get("/")
@with_user
def root():
    return render_template('index.html', user=g.user)


@app.route("/robots.txt")
def robotstxt():
    r = Response(response="User-Agent: *\nDisallow: /\n", status=200, mimetype="text/plain")
    r.headers["Content-Type"] = "text/plain; charset=utf-8"
    return r


@app.get("/<string:qid>/<logkey>")
@with_user
@with_logs
def logviewer_render(qid, logkey):
    return g.document.render_html(user=g.user)


@app.get("/evidence/<string:qid>/<logkey>")
@with_user
@with_logs_evidence
def logviewer_render_evidence(qid, logkey):
    return g.document.render_html(evidence=True, user=g.user)


@app.get("/api/raw/<string:qid>/<logkey>")
@with_logs
def api_raw_render(qid, logkey):
    return Response(g.document.render_plain_text(), mimetype="text/plain"), 200