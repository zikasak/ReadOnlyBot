from contextlib import contextmanager

from sqlalchemy.orm import sessionmaker


class DbWorker:

    def __init__(self, engine):
        self.engine = engine
        self.session = self.__get_session()

    @contextmanager
    def session_scope(self):
        ses = self.session()
        try:
            yield ses
            ses.commit()
        except:
            ses.rollback()
            raise
        finally:
            ses.close()

    def __get_session(self):
        return sessionmaker(bind=self.engine)
