import os
from django.apps import AppConfig
from django.conf import settings
import ProbQAInterop.ProbQA as probqa


class Pqawv1Config(AppConfig):
    name = 'pqawV1'
    verbose_name = 'Probabilistic Question Asking - Web, Version 1'

    # https://stackoverflow.com/questions/6791911/execute-code-when-django-starts-once-only
    def ready(self):
        print('Starting up for PID=%s...' % (os.getpid(),))
        # input('Attach the debugger and press ENTER')

        # Init SRLogger
        probqa.SRLogger.init(os.path.join(settings.BASE_DIR, '../../logs/PqaWeb'))

        from .pivot import Pivot
        Pivot.instance.reset_engine()
        print('Startup has finished.')
