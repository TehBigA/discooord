import datetime
import logging
import re
import threading
import sys
import warnings


try:
    import Queue
except ImportError:
    import queue as Queue


import decorator
import pytz


TIMEZONE_REGEX = re.compile(r'([-+])(\d\d):?(\d\d)$')
CACHED_TIMEZONES = {}

LOGGERS = {}
LOGGER_STDOUT_FORMAT = '[%(asctime)s] [%(name)s] [%(levelname)s] %(module)s - %(message)s'

MENTION_REGEX = re.compile(r'<(@[!&]?|#)(\d{17,21})>')
EMOJI_REGEX = re.compile(r'<:([\w\d_]+):(\d{17,21})>')

MENTION_TYPE_USER = '@'
MENTION_TYPE_NICKNAME = '@!'
MENTION_TYPE_CHANNEL = '#'
MENTION_TYPE_ROLE = '@&'


def get_logger(name, stdout=True, level=logging.INFO):
    if name in LOGGERS:
        return LOGGERS[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if stdout:
        formatter = logging.Formatter(LOGGER_STDOUT_FORMAT)
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(formatter)

    logger.addHandler(handler)

    LOGGERS[name] = logger

    return logger


_LOG = get_logger('discooord')


def is_unicode(s):
    return all(ord(c) >= 128 for c in s)


def parse_datetime(dt):
    if dt is None:
        return None

    search = TIMEZONE_REGEX.search(dt)

    if search:
        dt = dt[:search.start()]

        # Ugh.. timezones. (I want to support 2.7+)
        sign = 1 if search.group(1) == '+' else -1
        utcoffset = ((int(search.group(2)) * 60) + int(search.group(3))) * sign

        tzinfo = None
        if utcoffset in CACHED_TIMEZONES:
            tzinfo = CACHED_TIMEZONES[utcoffset]
        else:
            tzinfo = CACHED_TIMEZONES[utcoffset] = pytz.FixedOffset(utcoffset)

        parsed = datetime.datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%f')

        return parsed.replace(tzinfo=tzinfo)
    else:
        return datetime.datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%f')


class Bunch:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class Timer(object):
    '''Crude threaded repeating timer object'''

    thread = None
    running = None

    interval = 1
    background = True
    target = None
    args = None
    kwargs = None

    exception = None

    on_start = None
    on_stop = None
    on_exception = None

    def __init__(self, target=None, *args, **kwargs):
        self.running = Queue.Queue(maxsize=1)
        self._running_clear()

        self.interval = kwargs.pop('interval', 1)
        self.background = kwargs.pop('background', True)
        self.on_start = kwargs.pop('on_start', None)
        self.on_stop = kwargs.pop('on_stop', None)
        self.on_exception = kwargs.pop('on_exception', None)

        if target is not None:
            self.target = target

        self.args = args
        self.kwargs = kwargs

    def _running_clear(self, block=False):
        try:
            self.running.put(None, block=block)
        except:
            pass

    def _running_set(self, block=False, timeout=None):
        try:
            self.running.get(block=block, timeout=timeout)
        except:
            pass

    def start(self):
        if self.thread:
            return

        if self.on_start and self.on_start(self):
            return

        self._running_set()

        self.exception = None

        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = self.background

        self.thread.start()

    def stop(self):
        if self.on_stop and self.on_stop(self):
            return

        self._running_clear()

        if self.thread:
            self.thread.join()
            self.thread = None

    def run(self):
        self.exception = None

        self._run()
        self._running_clear()

        self.thread = None

    def _run(self):
        while self.running.empty():
            try:
                timeout = self.interval() if callable(self.interval) else self.interval
                self.running.get(timeout=timeout)
                return
            except Queue.Empty:
                try:
                    self.target(*self.args, **self.kwargs)
                except Exception as e:
                    _LOG.error('Timer exception ({})'.format(str(e)), exc_info=True)
                    self.exception = sys.exc_info()
                    if self.on_exception and self.on_exception(self):
                        return

    def is_running(self):
        return self.running.empty()


class ConditionalTimer(Timer):
    '''Timer will stop if `condition` is met. Condition is checked after execution. Runs at least once.'''

    condition = lambda: False

    def __init__(self, target=None, condition=None, *args, **kwargs):
        if self.condition is not None:
            self.condition = condition

        super(ConditionalTimer, self).__init__(target, *args, **kwargs)

    def _run(self):
        while self.running.empty():
            try:
                timeout = self.interval() if callable(self.interval) else self.interval
                self.running.get(timeout=timeout)
                return
            except Queue.Empty:
                self.target(*self.args, **self.kwargs)

                if self.condition():
                    if not self.on_stop or not self.on_stop(self):
                        self._running_clear()


class FiniteTimer(ConditionalTimer):
    '''Conditional timer which runs `n` times. Specify `run_count` kwarg.'''

    run_count = 10
    runs = 0

    def __init__(self, target=None, *args, **kwargs):
        self.run_count = kwargs.pop('run_count', 10)
        super(ConditionalTimer, self).__init__(target, *args, **kwargs)

    def condition(self):
        self.runs += 1
        return self.runs >= self.run_count


@decorator.decorator
def untested(fn, *args, **kwargs):
    warnings.warn('Untested function used! ({})'.format(str(fn)), stacklevel=3)
    return fn(*args, **kwargs)
