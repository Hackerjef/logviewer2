import os
import re

from flask import Blueprint, request, abort, current_app, send_file

from logviewer2.constants import Constants

Fproxy = Blueprint('fproxy', __name__, url_prefix='/fproxy')


@Fproxy.route('/FONT_WHITNEY_LIGHT')
@Fproxy.route('/FONT_WHITNEY_NORMAL')
@Fproxy.route('/FONT_WHITNEY_MEDIUM')
@Fproxy.route('/FONT_WHITNEYMEDIUM_MEDIUM')
@Fproxy.route('/FONT_WHITNEY_BOLD')
def rfproxy():
    match = re.match(Constants.RE_FPROXY_FACE, request.url_rule.rule)
    if match:
        if not match.groups()[0] in Constants.FONTS:
            return abort(404)
        try:
            abs_path = os.path.join(current_app.config['FDIR'].name, match.groups()[0])
            if not os.path.exists(abs_path):
                return abort(404)

            # Check if path is a file and serve
            if os.path.isfile(abs_path):
                return send_file(str(abs_path))
        except:
            return abort(404)
    else:
        return abort(404)
