from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid.request import Request

import backend.db_models as m
from backend.db_models import DBSession

@view_config(route_name='home', renderer='templates/mytemplate.jinja2')
def my_view(req: Request):
    return {'project': 'backend'}

@view_config(route_name='login')
def login_view(req: Request):
    uname = req.POST['username']
    passwd = req.POST['password']
    session = req.session
    user: m.FabUser = DBSession.query(m.AbstractUser).filter(username=uname)

    if user is not None and user.verify_password(passwd):
        new_token = user.refresh_session()

        session['uname'] = uname
        session['session_token'] = new_token

        return HTTPFound(req.params.get('return', '/'))
    else:
        return HTTPFound("/?login_failed=1")