from functools import wraps

from flask import current_app, abort, g, session, request, url_for, redirect
from oauthlib.oauth2 import InvalidClientError, TokenExpiredError, InvalidGrantError

from logviewer2.log_utils.models import LogEntry
from logviewer2.utils import GET_INSTANCE


def with_logs_evidence(fn):
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        gid, instid = None, None
        try:
            gid, instid = GET_INSTANCE(kwargs['qid'])
        except ValueError:
            abort(404)

        logkey = kwargs['logkey']
        db = current_app.db.get(gid, instid)
        if db is None:
            abort(404)

        plconfig = db.plugins.Logviewer2Companion.find_one({"_id": "config"}) or {}

        if not plconfig.get("allow_evidence_share", False):
            # if its not enabled or no plugin config
            abort(403)

        document = db.logs.find_one({"key": logkey})
        if not document:
            abort(404)
        g.document = LogEntry(document, evidence=True)
        g.document.internal_messages = []  # :) remove internal messages from class
        return fn(*args, **kwargs)

    return decorated_view


def with_logs(fn):
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        gid, instid = None, None
        try:
            gid, instid = GET_INSTANCE(kwargs['qid'])
        except ValueError:
            abort(404)

        logkey = kwargs['logkey']

        db = current_app.db.get(gid, instid)
        if db is None:
            abort(404)

        # get plugin config if exists
        plconfig = db.plugins.Logviewer2Companion.find_one({"_id": "config"}) or {}
        config = db.config.find_one({"guild_id": str(gid)}) or {}

        if plconfig.get("enabled", False):
            if not current_app.discord.authorized:
                session["next_url"] = request.path
                return redirect(url_for("auth.auth_discord"))

            try:
                current_user = current_app.discord.fetch_user()
            except (InvalidClientError, TokenExpiredError, InvalidGrantError):
                return redirect(url_for("auth.auth_discord"))

            if current_user.guild_members is not None:
                try:
                    guild_member = current_user.guild_members[gid]
                except (KeyError, IndexError):
                    try:
                        guild_member = current_user.fetch_guild_member(gid)
                    except AttributeError:
                        guild_member = None
            else:
                try:
                    guild_member = current_user.fetch_guild_member(gid)
                except AttributeError:
                    guild_member = None

            allowed_users = []
            allowed_roles_and_users = []
            if guild_member:
                allowed_roles_and_users += config.get("oauth_whitelist", [])

            for role in plconfig.get("allowed_roles", {}):
                allowed_users += plconfig.get("allowed_roles", {})[role]
            allowed_users += plconfig.get("allowed_users", [])

            allowed_role = False
            allowed_user = False
            if guild_member and guild_member.roles:
                for role in guild_member.roles:
                    if int(role) in allowed_roles_and_users:
                        allowed_role = True
                        break
                if current_user.id in allowed_roles_and_users or current_user.id in allowed_users:
                    allowed_user = True
                if not allowed_role and not allowed_user:
                    abort(403)
            elif current_user.id not in allowed_users:
                abort(403)

        document = db.logs.find_one({"key": logkey})
        if not document:
            abort(404)

        g.document = LogEntry(document)
        return fn(*args, **kwargs)

    return decorated_view


def authed(func):
    @wraps(func)
    def deco(*args, **kwargs):
        if not current_app.discord.authorized:
            abort(403)
        return func(*args, **kwargs)

    return deco


def with_user(func):
    @wraps(func)
    def deco(*args, **kwargs):
        if current_app.discord.authorized:
            try:
                user = current_app.discord.fetch_user()
            except (InvalidClientError, TokenExpiredError, InvalidGrantError):
                return redirect(url_for("auth.auth_discord"))
        else:
            user = None
        g.user = user
        return func(*args, **kwargs)

    return deco