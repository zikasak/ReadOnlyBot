import logging

from bt import Bt

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
bt = Bt()
bt.start_bot()
