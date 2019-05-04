import logging

from telegram.error import Unauthorized


def network_worker(func, pass_exception=False, **kwargs):
    tries = 5
    while tries:
        try:
            return func(**kwargs)
        except Unauthorized as ex:
            logging.warning(ex)
            if pass_exception:
                raise ex
            break
        except Exception as ex:
            tries -= 1
            if tries == 0 and pass_exception:
                raise ex
            logging.warning(ex)