import os
import sys
from datetime import datetime

import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from backend.db_models import DBSession, Base, FabUser, DoctorUser, PrintPost, PrintCommitment


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)

    with transaction.manager:
        user = FabUser("testuser", "test", "test@test.test", "Bob", "Bobson", "I am a human doing human things",
                       "USA", "California", "Los Angeles", "ender3", "excellent", "/static/human.png")
        DBSession.add(user)
        transaction.manager.commit()

        doc = DoctorUser("doccroc", "test", "doc@croc.com", "Doc", "Croc", "I really like reptiles", "USA", "Florida", "Orlando",
                         "Orlando Reptile Hospital", "University of Tampa", "Tail Repairs",
                         "/static/croc.png")
        DBSession.add(doc)
        transaction.manager.commit()

        print_post = PrintPost("hello make me a tail", "pls make tail thx", ["tail.stl"], doc, datetime.now(),
                               100)
        DBSession.add(print_post)
        transaction.manager.commit()

        print_commitment = PrintCommitment("hello yes i have made tail", 75, 10, ["tail_print.png"], user, print_post)
        DBSession.add(print_commitment)
        transaction.manager.commit()
