import os
from django.apps import AppConfig
from django.conf import settings
import ProbQAInterop.ProbQA as probqa


class Pqawv1Config(AppConfig):
    name = 'pqawV1'
    verbose_name = 'Probabilistic Question Asking - Web, Version 1'

    # https://stackoverflow.com/questions/6791911/execute-code-when-django-starts-once-only
    def ready(self):
        if os.environ.get('RUN_MAIN') != 'true':
            print('Exiting because detected running in reloader.')
            return

        print('Starting up for PID=%s...' % (os.getpid(),))
        # input('Attach the debugger and press ENTER')

        # Init SRLogger
        probqa.SRLogger.init(os.path.join(settings.BASE_DIR, '../../logs/PqaWeb'))

        from pqawV1.pivot import pivot_instance
        pivot_instance.reset_engine()
        pivot_instance.init_periodic_tasks()

        # Actually this doesn't work: sessions are never deleted from the DB by Django automatically.
        from .quiz_registry import QuizRegistry
        QuizRegistry.attach_session_expiration_handler()

        print('Startup has finished.')
