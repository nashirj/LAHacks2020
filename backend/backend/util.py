from pyramid.request import Request
from backend.db_models import DBSession, AbstractUser

import os
import uuid


def verify_user_token(req: Request):
    if req.session.get('uname') is None:
        return False

    user: AbstractUser = DBSession.query(AbstractUser).filter_by(username=req.session['uname']).first()
    if user is None:
        return False

    return user.verify_session(req.session['session_token'])


def get_user_geoloc(uname: str) -> dict:
    user: AbstractUser = DBSession.query(AbstractUser).filter_by(username=uname).first()
    geoloc = None
    if user is not None:
        geoloc = {
            'city': user.geo_location_city,
            'state': user.geo_location_state,
            'country': user.geo_location_cntry
        }

    return geoloc


def store_file_view(files_list):
    file_path_list = []

    for input in files_list:
        filename = input.filename
        input_file = input.file
        file_path = os.path.join('user_files', '%s.stl' % uuid.uuid4())
        temp_file_path = file_path + '~'

        input_file.seek(0)
        with open(temp_file_path, 'w+') as output_file:
            shutil.copyfileobj(input_file, output_file)

        os.rename(temp_file_path, file_path)
        file_path_list.append(file_path)

    return file_path_list
