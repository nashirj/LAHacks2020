from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, Column, Text, Boolean, ForeignKey, ARRAY, String
import from passlib import hash

import enum

Base = declarative_base()

class _AbstractUser(Base):
    username   = Column(Text, primary_key=True)
    email      = Column(Text)
    first_name = Column(Text)
    last_name  = Column(Text)

    geo_location_cntry = Column(Text)
    geo_location_state = Column(Text)
    geo_location_city  = Column(Text)

    _password_hash = Column(Text)
    _user_type = Column(Text)

    __tablename__ = 'users'
    __mapper_args__ = {
        'polymorphic_identity': 'base_user',
        'polymorphic_on': _user_type
    }

    def __init__(self, uname: str, password: str, email: str, fname: str, lname: str):
        self.username = uname
        self.email = email
        self.first_name  = fname
        self.last_name = lname

        self._password_hash = hash.pbkdf2_sha256.hash(password)

    def verify_password(self, password: str) -> bool:
        return hash.pbkdf2_sha256.hash(password) == self._password_hash

    def __repr__(self):
        return "<User(uname={uname}, fullname='{fname} {lname}', email={email}, user_type={usert}>".format(uname=self.username,
                                                                            fname=self.first_name, lname=self.last_name,
                                                                            email=self.email, usert=self._user_type)

class DoctorUser(_AbstractUser):
    username      = Column(Text, ForeignKey('base_user.username'), primary_key=True)
    hospital      = Column(Text)

    alma_mater     = Column(Text)
    specialization = Column(Text)
    biography      = Column(Text)

    __tablename__ = "doctors"
    __mapper_args__ = {
        'polymorphic_identity': 'doctor'
    }


class FabUser(_AbstractUser):
    username = Column(Text, ForeignKey('base_user.username'), primary_key=True)
    hospital = Column(Text)

    printer_model = Column(Text)
    filament_capable = Column(ARRAY(String))


    __tablename__ = "doctors"
    __mapper_args__ = {
        'polymorphic_identity': 'doctor'
    }


class FabUser(_AbstractUser):
    pass


class PrintRequest