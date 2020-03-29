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

    designs = []
    sorted_designs = list(DBSession.query.order_by(m.DesignPost.date_created.desc()))

    for design in sorted_designs:
        designs.append({
            'title': design.title,
            'uid': design.post_id,
            'body': design.body,
            'author': design.author_uname,
            'hospital': design.author.hospital,
            'files': design.get_files(),
            'date_created': str(design.date_created),
            'date_needed': str(design.date_need)
        })

    return {'is_logged_in': is_logged_in, 'user_name': req.session['uname'], 'page': 'browse_designs',
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


@view_config(route_name='register_fab')
def register_fab(req: Request):
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
    printer_model = data.get('printer model')
    print_quality = data.get('print quality')

    if uname and passwd and email and fname and lname and country and state and city and printer_model and print_quality:
        new_fab = m.FabUser(uname, passwd, email, fname, lname, country, state, city, printer_model, print_quality)

        DBSession.add(new_fab)
        DBSession.commit()

        new_token = new_fab.refresh_session()
        req.session['uname'] = uname
        req.session['session_token'] = new_token

        return HTTPFound(req.params.get('return', '/'))
    else:
        return HTTPBadRequest("Malformed request")


@view_config(route_name='view_print', renderer='templates/view_print.jinja2')
def view_print(req: Request):
    is_logged_in = verify_user_token(req)
    is_doctor = False

    if is_logged_in:
        user = DBSession.query(m.AbstractUser).filter_by(username=req.session['uname']).first()
        if user._user_type == "doctor":
            is_doctor = True

    post = DBSession.query(m.PrintPost).filter_by(req.matchdict['post_id']).first()

    commitments = []
    for resp in post.commitments:
        commitments.append({
            'author': resp.author_uname,
            'num_copies': resp.num_copies,
            'date_created': resp.date_created,
            'files': resp.get_files()
        })

    return {'is_logged_in': is_logged_in, 'user_name': req.session['uname'], 'page': 'view_print',
            'post': post, 'commitments': commitments, 'is_doctor': is_doctor}


@view_config(route_name='view_design', renderer='templates/view_design.jinja2')
def view_design(req: Request):
    is_logged_in = verify_user_token(req)
    is_doctor = False

    if is_logged_in:
        user = DBSession.query(m.AbstractUser).filter_by(username=req.session['uname']).first()
        if user._user_type == "doctor":
            is_doctor = True

    post = DBSession.query(m.DesignPost).filter_by(req.matchdict['post_id']).first()

    responses = []
    for resp in post.response:
        responses.append({
            'author': resp.author_uname,
            'date_created': resp.date_created,
            'is_accepted_response': resp.is_accepted_response,
            'files': resp.get_files()
        })

    return {'is_logged_in': is_logged_in, 'user_name': req.session['uname'], 'page': 'view_print',
            'post': post, 'responses': responses, 'is_doctor': is_doctor}

