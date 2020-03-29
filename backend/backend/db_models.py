import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy import Integer, Column, Text, Boolean, ForeignKey, ARRAY, String, PickleType, Date, func
from zope.sqlalchemy import register

import typing as T

from passlib import hash
import secrets
import uuid
import json


DBSession = scoped_session(sessionmaker())
register(DBSession)
Base = declarative_base()


class AbstractUser(Base):
    username = Column(String(75), primary_key=True)
    email = Column(String(75))
    first_name = Column(String(75))
    last_name = Column(String(75))

    geo_location_cntry = Column(String(75))
    geo_location_state = Column(String(75))
    geo_location_city = Column(String(75))

    _password_hash = Column(Text)
    _session_token_hash = Column(Text)
    _remember_me_token_hash = Column(Text)
    _user_type = Column(String(75))

    __tablename__ = "user"
    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": _user_type
    }

    def __init__(self, uname: T.AnyStr, password: T.AnyStr, email: T.AnyStr, fname: T.AnyStr, lname: T.AnyStr,
                 geo_country: T.AnyStr, geo_state: T.AnyStr, geo_city: T.AnyStr, user_type: T.AnyStr):
        self.username = uname
        self.email = email
        self.first_name = fname
        self.last_name = lname

        self.geo_location_cntry = geo_country
        self.geo_location_state = geo_state
        self.geo_location_city = geo_city

        self._user_type = user_type

        self._password_hash = hash.pbkdf2_sha256.hash(password)

    def generate_remember_me(self) -> str:
        token = secrets.token_urlsafe(32)
        self._remember_me_token_hash = hash.pbkdf2_sha256.hash(token)
        return token

    def verify_remember_me(self, token: T.AnyStr) -> bool:
        return hash.pbkdf2_sha256.verify(token, self._remember_me_token_hash)

    def refresh_session(self) -> str:
        token = secrets.token_urlsafe(32)
        self._session_token_hash = hash.pbkdf2_sha256.hash(token)
        return token

    def verify_session(self, token: T.AnyStr) -> bool:
        return hash.pbkdf2_sha256.verify(token, self._session_token_hash)

    def change_password(self, password: T.AnyStr) -> bool:
        self._password_hash = hash.pbkdf2_sha256.hash(password)

    def verify_password(self, password: T.AnyStr) -> bool:
        return hash.pbkdf2_sha256.verify(password, self._password_hash)

    def __repr__(self):
        return "<User(uname={uname}, fullname=\"{fname} {lname}\", email={email}, user_type={usert}>".format(
            uname=self.username,
            fname=self.first_name, lname=self.last_name,
            email=self.email, usert=self._user_type)


class DoctorUser(AbstractUser):
    username = Column(String(75), ForeignKey("user.username"), primary_key=True)
    hospital = Column(String(75))

    alma_mater = Column(String(75))
    specialization = Column(String(75))
    biography = Column(Text)

    design_posts = relationship("DesignPost", back_populates="author", uselist=True)
    print_posts = relationship("PrintPost", back_populates="author", uselist=True)

    def __init__(self, uname: T.AnyStr, password: T.AnyStr, email: T.AnyStr, fname: T.AnyStr, lname: T.AnyStr, geo_country: T.AnyStr,
                 geo_state: T.AnyStr, geo_city: T.AnyStr, hospital: T.AnyStr, alma_mater: T.AnyStr,
                 specialization: T.AnyStr, biography: T.AnyStr):
        self.hospital = hospital
        self.alma_mater = alma_mater
        self.specialization = specialization
        self.biography = biography

        super().__init__(uname, password, email, fname, lname, geo_country, geo_state, geo_city, "doctor")

    __tablename__ = "doctor"
    __mapper_args__ = {
        "polymorphic_identity": "doctor"
    }


class FabUser(AbstractUser):
    username = Column(Text, ForeignKey("user.username"), primary_key=True)
    hospital = Column(Text)

    design_responses = relationship("DesignResponse", back_populates="author", uselist=True)
    print_commitments = relationship("PrintCommitment", back_populates="author", uselist=True)

    printer_model = Column(Text)
    print_quality_capable = Column(Integer)  # This should be a number out of 10

    def __init__(self, uname: T.AnyStr, password: T.AnyStr, email: T.AnyStr, fname: T.AnyStr, lname: T.AnyStr,
                 geo_country: T.AnyStr, geo_state: T.AnyStr, geo_city: T.AnyStr, printer_model: T.AnyStr,
                 print_quality_capable: T.AnyStr):
        self.printer_model = printer_model
        self.print_quality_capable = print_quality_capable

        super().__init__(uname, password, email, fname, lname, geo_country, geo_state, geo_city, "fabricator")

    __tablename__ = "fabricator"
    __mapper_args__ = {
        "polymorphic_identity": "fabricator"
    }


class DesignPost(Base):
    post_id = Column(String(32), primary_key=True)
    title = Column(String(75))
    body = Column(Text)
    _files_json = Column(Text)
    files = list()
    has_accepted_response = Column(Boolean)
    date_created = Column(Date)
    date_needed = Column(Date)

    author_uname = Column(String(75), ForeignKey("doctor.username"))
    author = relationship("DoctorUser", back_populates="design_posts")
    responses = relationship("DesignResponse", back_populates="parent_post", uselist=True)

    __tablename__ = "design_post"

    def __init__(self, title: T.AnyStr, body: T.AnyStr, files: T.List[str], author: AbstractUser, date: Date):
        self.title = title
        self.body = body
        self.author = author

        self.files = files
        self._files_json= json.dumps({'files': self.files})
        self.post_id = uuid.uuid4().hex

        self.has_accepted_response = False

        self.date_created = func.current_date()
        self.date_needed = date

    def load_files(self):
        self.files = json.loads(self._files_json)['files']

    def get_files(self):
        self.load_files()
        return self.files


class DesignResponse(Base):
    resp_id = Column(String(32), primary_key=True)
    body = Column(Text)
    _files_json = Column(Text)
    files = list()
    is_accepted_response = Column(Boolean)
    date_created = Column(Date)

    author_uname = Column(String(75), ForeignKey("fabricator.username"))
    author = relationship("FabUser", back_populates="design_responses")

    parent_post_id = Column(String(75), ForeignKey("design_post.post_id"))
    parent_post = relationship("DesignPost", back_populates="responses")

    __tablename__ = "design_reponse"

    def __init__(self, body: T.AnyStr, files: T.List[str], author: FabUser, parent: DesignPost):
        self.body = body
        self.author = author
        self.parent_post = parent

        self.files = files
        self._files_json = json.dumps({'files': self.files})

        self.is_accepted_response = False

        self.date_created = func.current_date()

        self.resp_id = uuid.uuid4().hex

    def load_files(self):
        self.files = json.loads(self._files_json)['files']


class PrintPost(Base):
    post_id = Column(String(32), primary_key=True)
    title = Column(String(75))
    body = Column(Text)
    num_parts_needed = Column(Integer)

    _files_json = Column(Text)
    files = list()

    date_created = Column(Date)
    date_needed = Column(Date)

    author_uname = Column(String(75), ForeignKey("doctor.username"))
    author = relationship("DoctorUser", back_populates="print_posts")
    commitments = relationship("PrintCommitment", back_populates="parent_post", uselist=True)

    __tablename__ = "print_post"

    def __init__(self, title: T.AnyStr, body: T.AnyStr, files: list, author: AbstractUser,
                 date: Date, num_parts_needed: int):
        self.title = title
        self.body = body
        self.author = author
        self.num_parts_needed = num_parts_needed

        self.files = files
        self._files_json = json.dumps({'files': self.files})

        self.post_id = uuid.uuid4().hex

        self.date_created = datetime.datetime.now()
        self.date_needed = date

    def load_files(self):
        self.files = json.loads(self._files_json)['files']

    def get_files(self):
        self.load_files()
        return self.files


class PrintCommitment(Base):
    resp_id = Column(String(32), primary_key=True)
    body = Column(Text)
    num_copies = Column(Integer)
    est_time_days = Column(Integer)
    is_verified_print = Column(Boolean)
    is_verified_recv = Column(Boolean)
    date_created = Column(Date)

    author_uname = Column(String(75), ForeignKey("fabricator.username"))
    author = relationship("FabUser", back_populates="print_commitments")

    parent_post_id = Column(String(75), ForeignKey("print_post.post_id"))
    parent_post = relationship("PrintPost", back_populates="commitments")

    __tablename__ = "print_commitments"

    def __init__(self, body: T.AnyStr, num_copies: int, est_time_days: int, author: FabUser, parent: PrintPost):
        self.body = body
        self.num_copies = num_copies
        self.est_time_days = est_time_days
        self.author = author
        self.parent_post = parent

        self.date_created = datetime.datetime.now()

        self.resp_id = uuid.uuid4().hex

