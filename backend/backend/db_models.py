from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Integer, Column, Text, Boolean, ForeignKey, ARRAY, String
from passlib import hash

Base = declarative_base()


class _AbstractUser(Base):
    username = Column(String(75), primary_key=True)
    email = Column(String(75))
    first_name = Column(String(75))
    last_name = Column(String(75))

    geo_location_cntry = Column(String(75))
    geo_location_state = Column(String(75))
    geo_location_city = Column(String(75))

    _password_hash = Column(Text)
    _user_type = Column(String(75))

    __tablename__ = "user"
    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": _user_type
    }

    def __init__(self, uname: str, password: str, email: str, fname: str, lname: str, geo_country: str, geo_state: str,
                 geo_city: str, user_type: str):
        self.username = uname
        self.email = email
        self.first_name = fname
        self.last_name = lname

        self.geo_location_cntry = geo_country
        self.geo_location_state = geo_state
        self.geo_location_city = geo_city

        self._user_type = user_type

        self._password_hash = hash.pbkdf2_sha256.hash(password)

    def verify_password(self, password: str) -> bool:
        return hash.pbkdf2_sha256.hash(password) == self._password_hash

    def __repr__(self):
        return "<User(uname={uname}, fullname=\"{fname} {lname}\", email={email}, user_type={usert}>".format(
            uname=self.username,
            fname=self.first_name, lname=self.last_name,
            email=self.email, usert=self._user_type)


class DoctorUser(_AbstractUser):
    username = Column(String(75), ForeignKey("user.username"), primary_key=True)
    hospital = Column(String(75))

    alma_mater = Column(String(75))
    specialization = Column(String(75))
    biography = Column(Text)

    design_posts = relationship("DesignPost", back_populates="author", uselist=True)
    print_posts = relationship("PrintPost", back_populates="author", uselis=True)

    def __init__(self, uname: str, password: str, email: str, fname: str, lname: str, geo_country: str,
                 geo_state: str, geo_city: str, hospital: str, alma_mater: str, specialization: str, biography: str):
        self.hospital = hospital
        self.alma_mater = alma_mater
        self.specialization = specialization
        self.biography = biography

        super().__init__(uname, password, email, fname, lname, geo_country, geo_state, geo_city, "doctor")

    __tablename__ = "doctor"
    __mapper_args__ = {
        "polymorphic_identity": "doctor"
    }


class FabUser(_AbstractUser):
    username = Column(Text, ForeignKey("user.username"), primary_key=True)
    hospital = Column(Text)

    design_responses = relationship("DesignResponse", back_populates="author", use_list=True)
    print_commitments = relationship("PrintCommitment", back_populates="author", use_list=True)

    printer_model = Column(Text)
    filament_capable = Column(ARRAY(String(10)))
    print_quality_capable = Column(Integer)  # This should be a number out of 10

    def __init__(self, uname: str, password: str, email: str, fname: str, lname: str, geo_country: str,
                 geo_state: str, geo_city: str, printer_model: str, filament_capable: list, print_quality_capable: str):
        self.printer_model = printer_model
        self.filament_capable = filament_capable
        self.print_quality_capable = print_quality_capable

        super().__init__(uname, password, email, fname, lname, geo_country, geo_state, geo_city, "fabricator")

    __tablename__ = "fabricator"
    __mapper_args__ = {
        "polymorphic_identity": "fabricator"
    }


class DesignPost(Base):
    post_id = Column(String(75))
    title = Column(String(75))
    body = Column(Text)
    files = Column(ARRAY(String(20)))
    has_accepted_response = Column(Boolean)

    author_uname = Column(String(75), ForeignKey("doctor.username"))
    author = relationship("DoctorUser", back_populates="posts")
    responses = relationship("DesignResponse", back_populates="post", use_list=True)

    __tablename__ = "design_post"

    def __init__(self, title: str, body: str, images: list, author_uname: str, author: _AbstractUser):
        self.title = title
        self.body = body
        self.images = images
        self.author = author


class DesignResponse(Base):
    body = Column(Text)
    files = Column(ARRAY(String(20)))
    is_accepted_response = Column(Boolean)

    author_uname = Column(String(75), ForeignKey("fabricator.username"))
    author = relationship("FabUser", back_populates="post_responses")

    parent_post_id = Column(String(75), ForeignKey("design_post.post_id"))
    parent_post = relationship("DesignPost", back_populates="design_responses")

    __tablename__ = "design_reponse"


class PrintPost(Base):
    post_id = Column(String(75))
    title = Column(String(75))
    body = Column(Text)
    files = Column(ARRAY(String(20)))

    author_uname = Column(String(75), ForeignKey("doctor.username"))
    author = relationship("DoctorUser", back_populates="posts")
    commitments = relationship("PrintCommitment", back_populates="post", use_list=True)

    __tablename__ = "print_post"

    def __init__(self, title: str, body: str, images: list, author_uname: str, author: _AbstractUser):
        self.title = title
        self.body = body
        self.images = images
        self.author = author


class PrintCommitment(Base):
    body = Column(Text)
    num_copies = Column(Integer)
    est_time_days = Column(Integer)
    is_verified_print = Column(Boolean)
    is_verified_recv = Column(Boolean)

    author_uname = Column(String(75), ForeignKey("fabricator.username"))
    author = relationship("FabUser", back_populates="print_commitments")

    parent_post_id = Column(String(75), ForeignKey("print_post.post_id"))
    parent_post = relationship("PrintPost", back_populates="print_commitments")

    __tablename__ = "print_commitments"
