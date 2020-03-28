from pyramid.httpexceptions import HTTPFound, HTTPForbidden, HTTPMethodNotAllowed
from pyramid.view import view_config
from pyramid.request import Request

import backend.db_models as m
from backend.db_models import DBSession
from backend.util import verify_user_token, get_user_geoloc


@view_config(route_name='home', renderer='templates/mytemplate.jinja2')
def my_view(req: Request):
    return {'project': 'backend'}


@view_config(route_name='login')
def login_view(req: Request):
    if req.method != 'POST':
        return HTTPMethodNotAllowed("This route only valid for POST request")

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


@view_config(route_name='browse_prints', renderer='templates/browse_prints.jinja2')
def browse_prints_view(req: Request):
    is_logged_in = verify_user_token(req)

    prints = []
    if is_logged_in:
        user_loc_data = get_user_geoloc(req.session['uname'])
        doctors_matching_loc = list(DBSession.query(m.DoctorUser).filter_by(geo_location_cntry=user_loc_data['country'],
                                                                            geo_location_state=user_loc_data['state'],
                                                                            geo_location_city=user_loc_data['city']))
        for doc in doctors_matching_loc:
            for post in doc.design_posts:
                responses = []

                prints.append({
                    'title': post.title,
                    'body': post.body,
                    'author': post.author_uname,
                    'files': post.get_files()
                })
    else:
        # TODO: fix this later, temporary code only displays one doctor's posts if not logged in
        posts = DBSession.query(m.DoctorUser).first().posts
        for post in posts:
            prints.append({
                'title': post.title,
                'body': post.body,
                'author': post.author_uname,
                'files': post.get_files()
            })

    return {'user_name': req.session['uname'], 'page': 'browse_prints', 'prints_display': prints}


# This snippet is for viewing a particular print, I wrote it in the wrong location, so I'm leaving it here for later
# for resp in post.responses:
#     responses.append({
#         'author': resp.author_uname,
#         'files': resp.get_files()
#     })
