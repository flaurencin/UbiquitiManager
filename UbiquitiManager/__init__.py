import logging

__title__ = 'UbiquitiManager'
__version__ = '0.0.2'
__author__ = 'Frederic Laurencin'
__author_email__ = 'flaurencin@free.fr'
__license__ = 'http://www.apache.org/licenses/LICENSE-2.0'
__copyright__ = 'Copyright 2016 Frederic Laurencin'

try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
