from flask import Blueprint, current_app, redirect, session, url_for, request
from oauthlib.oauth2 import InvalidClientError, TokenExpiredError, MismatchingStateError, InvalidGrantError

from logviewer2.utils.decos import authed

Auth = Blueprint('auth', __name__, url_prefix='/api/auth')


@Auth.route('/logout', methods=["GET", "POST"])
@authed
def auth_discord_logout():
    current_app.discord.revoke()
    session.clear()  # Clear the session on logout
    return redirect(url_for("root"))


@Auth.get('/discord')
def auth_discord():
    next_url = request.args.get('next', None)
    if next_url:
        session['next_url'] = next_url
    return current_app.discord.create_session(
        scope=["identify", "email", "guilds", "guilds.members.read", "connections"], prompt=False)


@Auth.get('/discord/callback')
def auth_discord_callback():
    try:
        token = current_app.discord.callback()
        session['oauth_token'] = token
    except MismatchingStateError:
        return redirect(url_for("auth.auth_discord"))
    except InvalidClientError as e:
        print(f"Invalid client error: {e}")
        return redirect(url_for("auth.auth_discord"))
    except TokenExpiredError as e:
        print(f"Token expired error: {e}")
        return redirect(url_for("auth.auth_discord"))
    except InvalidGrantError as e:
        print(f"Invalid grant error: {e}")
        return redirect(url_for("auth.auth_discord"))

    if 'next_url' in session:
        url = session.pop('next_url')
        return redirect(url)
    return redirect(url_for("root"))


@Auth.get('/@me')
@authed
def auth_me():
    try:
        data = dict(current_app.discord.fetch_user().__dict__)
    except (InvalidClientError, TokenExpiredError, InvalidGrantError):
        return redirect(url_for("auth.auth_discord"))
    for k in list(data.keys()):
        if k.startswith('_'):
            del data[k]
    return data