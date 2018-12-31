import os
from django.apps import AppConfig
from django.conf import settings
import ProbQAInterop.ProbQA as probqa

class Pqawv1Config(AppConfig):
    name = 'pqawV1'
    verbose_name = 'Probabilistic Question Asking - Web, Version 1'
    # https://stackoverflow.com/questions/6791911/execute-code-when-django-starts-once-only
    def ready(self):
        print('Startup of subsystems...')
        # Init SRLogger
        probqa.SRLogger.init(os.path.join(settings.BASE_DIR, '../../logs/PqaWeb'))
        # Load ProbQA engine
        print('All subsystems operational!')