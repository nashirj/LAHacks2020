from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory

from sqlalchemy import engine_from_config
from backend.db_models import DBSession, Base


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    session_factory = SignedCookieSessionFactory('this is a secret don\'t tell nobody')

    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')
    config.set_session_factory(session_factory)

    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.scan()

    return config.make_wsgi_app()

