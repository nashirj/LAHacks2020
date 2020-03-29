from pyramid.httpexceptions import HTTPFound, HTTPForbidden, HTTPMethodNotAllowed, HTTPBadRequest, HTTPUnauthorized, \
    HTTPNotFound
from pyramid.renderers import render_to_response
from pyramid.view import view_config
from pyramid.request import Request
from sqlalchemy import func

import backend.db_models as m
from backend.db_models import DBSession
from backend.util import verify_user_token, get_user_geoloc

import datetime

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


@view_config(route_name='view_profile', renderer="")
def profile_view(req: Request):
    uname = None
    is_logged_in = False
    if verify_user_token(req):
        uname = req.session['uname']
        is_logged_in = True

    query_uname = req.matchdict['uname_query']
    query_user: m.AbstractUser = DBSession.query(m.AbstractUser).filter_by(username=query_uname).first()
    if query_user is None:
        return HTTPNotFound("User not found")

    renderer = None
    query_data = {
        'profile_pic': query_user.profile_pic,
        'username': query_user.username,
        'fname': query_user.first_name,
        'lname': query_user.last_name,
        'email': query_user.email,
        'country': query_user.geo_location_cntry,
        'state': query_user.geo_location_state,
        'city': query_user.geo_location_city,
        'bio': query_user.biography
    }

    if query_user._user_type == "doctor":
        query_user: m.DoctorUser = DBSession.query(m.DoctorUser).filter_by(username=query_uname)
        renderer = "templates/profiles/doc_profile.jinja2"

        query_data.update({
            'hospital': query_user.hospital,
            'alma_mater': query_user.alma_mater,
            'specialization': query_user.specialization,
        })
    else:
        query_user: m.FabUser = DBSession.query(m.FabUser).filter_by(username=query_uname)
        renderer = "templates/profiles/fab_profiles.jinja2"

        designs = []
        for design in query_user.design_responses:
            designs.append({
                'title': design.parent_post.title,
                'date': design.date_created,
                'desc': design.body,
                'image': design.get_files()[0]
            })

        prints = []
        for print in query_user.print_commitments:
            prints.append({
                'title': print.parent_post.title,
                'date': print.date_created,
                'desc': print.body,
                'image': print.get_files()[0]
            })

        query_data.update({
            'fab_capabilities': query_user.printer_model,
            'expected_quality': query_user.print_quality_capable,
            'designs': designs,
            'prints': prints
        })

    render_to_response(renderer, {
        'is_logged_in': is_logged_in,
        'user_name': uname,
        'query_user_data': query_data
    }, req)


@view_config(route_name='browse_prints', renderer='templates/browse/browse_prints.jinja2')
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


@view_config(route_name='browse_designs', renderer='templates/browse/browse_designs.jinja2')
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


@view_config(route_name='view_print', renderer='templates/view/view_print.jinja2')
def view_print(req: Request):
    is_logged_in = verify_user_token(req)
    is_doctor = False
    is_post_owner = False

    post = DBSession.query(m.PrintPost).filter_by(post_id=req.matchdict['post_id']).first()

    post_info = {
        'title': post.title,
        'body': post.body,
        'files': post.get_files(),
        'date_created': post.date_created,
        'date_needed': post.date_needed,
        'author': post.author_uname
    }

    if is_logged_in:
        user = DBSession.query(m.AbstractUser).filter_by(username=req.session['uname']).first()
        if user._user_type == "doctor":
            is_doctor = True
        if user.username == post.doctor_uname:
            is_post_owner = True

    num_parts_in_progress = 0
    num_parts_completed = 0
    commitments = []
    for resp in post.commitments:
        if resp.is_verified_print:
            num_parts_completed += resp.num_copies
        else:
            num_parts_in_progress += resp.num_copies

        commitments.append({
            'author': resp.author_uname,
            'num_copies': resp.num_copies,
            'date_created': resp.date_created,
            'files': resp.get_files()
        })

    part_num_info = {
        'needed': post.num_parts_needed,
        'completed': num_parts_completed,
        'in_progress': num_parts_in_progress,
        'not_started': (post.num_parts_needed - num_parts_in_progress - num_parts_completed)
    }

    return {'is_logged_in': is_logged_in, 'user_name': req.session['uname'], 'page': 'view_print',
            'hospital': post.author.hospital, 'post': post_info, 'commitments': commitments,
            'is_doctor': is_doctor, 'is_post_owner': is_post_owner, 'part_num_info': part_num_info}


@view_config(route_name='view_design', renderer='templates/view_design.jinja2')
def view_design(req: Request):
    is_logged_in = verify_user_token(req)
    is_doctor = False
    is_post_owner = False

    post = DBSession.query(m.DesignPost).filter_by(post_id=req.matchdict['post_id']).first()

    post_info = {
        'title': post.title,
        'body': post.body,
        'files': post.get_files(),
        'has_accepted_response': post.has_accepted_response,
        'date_created': post.date_created,
        'date_needed': post.date_needed,
        'author': post.author_uname
    }

    if is_logged_in:
        user = DBSession.query(m.AbstractUser).filter_by(username=req.session['uname']).first()
        if user._user_type == "doctor":
            is_doctor = True
        if user.username == post.doctor_uname:
            is_post_owner = True

    responses = []
    for resp in post.response:
        responses.append({
            'author': resp.author_uname,
            'date_created': resp.date_created,
            'is_accepted_response': resp.is_accepted_response,
            'files': resp.get_files()
        })

    return {'is_logged_in': is_logged_in, 'user_name': req.session['uname'], 'page': 'view_print',
            'hospital': post.author.hospital, 'post': post_info, 'responses': responses,
            'is_doctor': is_doctor, 'is_post_owner': is_post_owner}


@view_config(route_name='submit_print_page', renderer='templates/submit/submit_print.jinja2')
def submit_print_page(req: Request):
    is_logged_in = verify_user_token(req)
    user = DBSession.query(m.FabUser).filter_by(username=req.session['username'])
    if not is_logged_in or not user:
        return HTTPUnauthorized("You must be logged in to view this page")

    return {'is_logged_in': is_logged_in, 'user_name': user.username}


@view_config(route_name='submit_print')
def submit_print(req: Request):
    if req.method != 'POST':
        return HTTPMethodNotAllowed("This route only valid for POST request")

    post = DBSession.query(m.PrintPost).filter_by(post_id=req.matchdict['post_id']).first()
    data = req.POST
    num_parts = data.get('num_items')
    date_completed = datetime.fromisoformat(data.get('completion-date'))

    if num_parts and date_completed:
        new_print_submission = m.PrintCommitment("", num_parts, date_completed, req.session['uname'], post)

        DBSession.add(new_print_submission)
        DBSession.commit()

        return HTTPFound(req.params.get('return', '/'))
    else:
        return HTTPBadRequest("Malformed request")


@view_config(route_name='submit_design')
def submit_design(req: Request):
    if req.method != 'POST':
        return HTTPMethodNotAllowed("This route only valid for POST request")

    post = DBSession.query(m.DesignPost).filter_by(post_id=req.matchdict['post_id']).first()
    data = req.POST
    body = data.get('print-notes')
    files = data.get('files')

    if body and files:
        new_design_submission = m.DesignResponse(body, files, req.session['uname'], post)

        DBSession.add(new_design_submission)
        DBSession.commit()

        return HTTPFound(req.params.get('return', '/'))
    else:
        return HTTPBadRequest("Malformed request")


