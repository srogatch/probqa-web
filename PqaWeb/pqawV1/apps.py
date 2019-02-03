import os
from django.apps import AppConfig
from django.conf import settings
import ProbQAInterop.ProbQA as probqa


class Pqawv1Config(AppConfig):
    name = 'pqawV1'
    verbose_name = 'Probabilistic Question Asking - Web, Version 1'

    # https://stackoverflow.com/questions/6791911/execute-code-when-django-starts-once-only
    def ready(self):
        env_run_main=os.environ.get('RUN_MAIN')
        print('IS_PRODUCTION=%s, RUN_MAIN=%s' % (settings.IS_PRODUCTION, env_run_main))
        if (not settings.IS_PRODUCTION) and (env_run_main != 'true'):
            print('Exiting because detected running in reloader.')
            return

        print('Starting up for PID=%s...' % (os.getpid(),))
        # input('Attach the debugger and press ENTER')

        # Init SRLogger
        probqa.SRLogger.init(os.path.join(settings.BASE_DIR, '../../logs/PqaWeb'))

        # Generate thumbnails for targets which don't have them
        from .models import Target
        from django.db.models import Q
        from .thumbnails import refresh_thumbnail
        no_tn_targets = Target.objects.filter(Q(thumbnail__isnull=True) | Q(thumbnail=''))
        for ntt in no_tn_targets:
            refresh_thumbnail(ntt)

        from pqawV1.pivot import pivot_instance
        pivot_instance.reset_engine()
        pivot_instance.init_periodic_tasks()

        # Actually this doesn't work: sessions are never deleted from the DB by Django automatically.
        from .quiz_registry import QuizRegistry
        QuizRegistry.attach_session_expiration_handler()

        print('Startup has finished.')
