from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, Column, Text, Boolean, ForeignKey, ARRAY, String(75)
import from passlib import hash

import enum

Base = declarative_base()

class _AbstractUser(Base):
    username   = Column(String(75), primary_key=True)
    email      = Column(String(75))
    first_name = Column(String(75))
    last_name  = Column(String(75))

    geo_location_cntry = Column(String(75))
    geo_location_state = Column(String(75))
    geo_location_city  = Column(String(75))

    _password_hash = Column(String(75))
    _user_type = Column(String(75))

    __tablename__ = 'users'
    __mapper_args__ = {
        'polymorphic_identity': 'base_user',
        'polymorphic_on': _user_type
    }

    def __init__(self, uname: str, password: str, email: str, fname: str, lname: str, geo_country: str, geo_state: str,
                 geo_city: str, user_type: str):
        self.username    = uname
        self.email       = email
        self.first_name  = fname
        self.last_name   = lname

        self.geo_location_cntry = geo_country
        self.geo_location_state = geo_state
        self.geo_location_city  = geo_city

        self._user_type = user_type

        self._password_hash = hash.pbkdf2_sha256.hash(password)

    def verify_password(self, password: str) -> bool:
        return hash.pbkdf2_sha256.hash(password) == self._password_hash

    def __repr__(self):
        return "<User(uname={uname}, fullname='{fname} {lname}', email={email}, user_type={usert}>".format(uname=self.username,
                                                                            fname=self.first_name, lname=self.last_name,
                                                                            email=self.email, usert=self._user_type)

class DoctorUser(_AbstractUser):
    username      = Column(String(75), ForeignKey('base_user.username'), primary_key=True)
    hospital      = Column(String(75))

    alma_mater     = Column(String(75))
    specialization = Column(String(75))
    biography      = Column(Text)

    def __init__(self, uname: str, password: str, email: str, fname: str, lname: str, geo_country: str,
                 geo_state: str, geo_city: str, hospital: str, alma_mater: str, specialization: str, biography: str):
        self.hospital = hospital
        self.alma_mater = alma_mater
        self.specialization = specialization
        self.biography = biography

        super().__init__(uname, password, email, fname, lname, geo_country, geo_state, geo_city, "Doctor")

    __tablename__ = "doctors"
    __mapper_args__ = {
        'polymorphic_identity': 'doctor'
    }


class FabUser(_AbstractUser):
    username = Column(Text, ForeignKey('base_user.username'), primary_key=True)
    hospital = Column(Text)

    printer_model         = Column(Text)
    filament_capable      = Column(ARRAY(String(10)))
    print_quality_capable = Column(Integer) # This should be a number out of 10

    def __init__(self, uname: str, password: str, email: str, fname: str, lname: str, geo_country: str,
                 geo_state: str, geo_city: str, printer_model: str, filament_capable: list, print_quality_capable: str):
        self.printer_model         = printer_model
        self.filament_capable      = filament_capable
        self.print_quality_capable = print_quality_capable

        super().__init__(uname, password, email, fname, lname, geo_country, geo_state, geo_city, "Fabricator")

    __tablename__ = "fabricators"
    __mapper_args__ = {
        'polymorphic_identity': 'fabricator'
    }


class _AbstractPost():
    title = Column(String(75))


class PrintRequest:
    pass