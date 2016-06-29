import os, sys
from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker, MultiService
from twisted.application import internet

class Options(usage.Options):
    optParameters = [
        ["conf", "c", "config.ini", "Configuration file path"],
        ["timers", "t", "timers", "Timers module path"],
    ]

class Service(object):
    implements(IServiceMaker, IPlugin)

    def __init__(self, name, description, options):
        Service.tapname = name
        Service.description = description
        Service.options = options

    def makeService(self, options):
        if not os.path.exists(options['conf']):
            raise OSError("Config File %s not found" % options['conf'])

        ms = MultiService()
        for step, callback in build_timers(options['timers']):
            svr = internet.TimerService(step, callback, options)
            svr.setServiceParent(ms)

        return ms

def build_timers(timer_path):
    try:
        mod = _import(timer_path)
    except:
        import traceback
        traceback.print_exc()
        sys.stderr.write('Ignoring %.py\n' % (timer_path))
        return []

    timers = []
    for timer in getattr(mod, 'TIMERS'):
        timers.append((int(timer[0]), _import(timer[1], False)))

    return timers

def _import(module_path, module = True):
    sp = module_path.split('.')
    if not module:
        module_path = '.'.join(sp[:-1])
    mod = __import__(module_path)
    for m in sp[1:]:
        mod = getattr(mod, m)
    return mod

serviceMaker = Service("announcer", "Presto Announcer Service", Options)
