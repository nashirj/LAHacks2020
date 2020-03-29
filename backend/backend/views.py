from pyramid.httpexceptions import HTTPFound, HTTPForbidden, HTTPMethodNotAllowed, HTTPBadRequest
from pyramid.view import view_config
from pyramid.request import Request
from sqlalchemy import func

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
            for post in doc.print_posts:
                responses = []

                prints.append({
                    'title': post.title,
                    'uid': post.post_id,
                    'body': post.body,
                    'author': post.author_uname,
                    'hospital': doc.hospital,
                    'files': post.get_files()
                })
    else:
        # TODO: fix this later, temporary code only displays one doctor's posts if not logged in
        doc = DBSession.query(m.DoctorUser).first()
        posts = doc.print_posts
        for post in posts:
            prints.append({
                'title': post.title,
                'uid': post.post_id,
                'body': post.body,
                'author': post.author_uname,
                'files': post.get_files(),
                'date_created': str(post.date_created),
                'date_needed': str(post.date_needed)
            })

    return {'is_logged_in': is_logged_in, 'user_name': req.session['uname'], 'page': 'browse_prints',
            'prints_display': prints}


@view_config(route_name='browse_designs', renderer='templates/browse_designs.jinja2')
def browse_designs_view(req: Request):
    is_logged_in = verify_user_token(req)

    designs = list(DBSession.query.order_by(m.DesignPost.date_created.desc()))

    return {'is_logged_in': is_logged_in, 'user_name': req.session['uname'], 'page': 'Browse Designs',
            'designs_display': designs}


@view_config(route_name='register_doctor')
def register_doctor(req: Request):
    if req.method != 'POST':
        return HTTPMethodNotAllowed("This route only valid for POST request")

    data = req.POST
    uname = data.get('uname')
    passwd = data.get('password')
    email = data.get('email')
    fname = data.get('fname')
    lname = data.get('lname')
    country = data.get('country')
    state = data.get('state')
    city = data.get('city')
    hospital = data.get('hospital')
    alma_mater = data.get('alma_mater')
    spec = data.get('specialization')
    bio = data.get('bio')

    if uname and passwd and email and fname and lname and country and state and city and hospital and alma_mater \
            and spec and bio:
        new_doctor = m.DoctorUser(uname, passwd, email, fname, lname, country, state, city, hospital, alma_mater,
                                  spec, bio)
        DBSession.add(new_doctor)
        DBSession.commit()

        new_token = new_doctor.refresh_session()
        req.session['uname'] = uname
        req.session['session_token'] = new_token

        return HTTPFound(req.params.get('return', '/'))
    else:
        return HTTPBadRequest("Malformed request")


@view_config(route_name='register_fab', renderer='templates/register_fab.jinja2')
def register_rab(req: Request):
    new_fab = m.FabUser(req.params['uname'], req.params['password'], req.params['email'], req.params['fname'],
                        req.params['lname'], req.params['country'], req.params['state'], req.params['city'],
                        req.params['printer model'], req.params['print quality'])

    DBSession.add(new_fab)
    DBSession.commit()

    # TODO: Return something here


# This snippet is for viewing a particular print, I wrote it in the wrong location, so I'm leaving it here for later
# for resp in post.responses:
#     responses.append({
#         'author': resp.author_uname,
#         'files': resp.get_files()
#     })
