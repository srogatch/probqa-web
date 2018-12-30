from django.apps import AppConfig
import ProbQAInterop.ProbQA as probqa

class Pqawv1Config(AppConfig):
    name = 'pqawV1'
    verbose_name = 'Probabilistic Question Asking - Web, Version 1'
    # https://stackoverflow.com/questions/6791911/execute-code-when-django-starts-once-only
    def ready(self):
        print('Startup of subsystems...')
        # Load ProbQA engine
        print('All subsystems operational!')