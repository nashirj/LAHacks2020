from pyramid.request import Request
from backend.db_models import DBSession, AbstractUser


def verify_user_token(req: Request):
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
