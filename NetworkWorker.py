import logging

from telegram.error import Unauthorized


def network_worker(fun, **args):
    tries = 5
    while tries:
        try:
            return fun(**args)
        except Unauthorized as ex:
            logging.warning(ex)
            break
        except Exception as ex:
            tries -= 1
            logging.warning(ex)
    return None
