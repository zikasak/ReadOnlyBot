import logging

from telegram.error import Unauthorized


def network_worker(fun, passException=False, **args):
    tries = 5
    while tries:
        try:
            return fun(**args)
        except Unauthorized as ex:
            logging.warning(ex)
            if passException:
                raise ex
            break
        except Exception as ex:
            tries -= 1
            if tries == 0 and passException:
                raise ex
            logging.warning(ex)
    return None
