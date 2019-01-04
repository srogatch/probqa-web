import os
from django.apps import AppConfig
from django.conf import settings
import ProbQAInterop.ProbQA as probqa

class Pqawv1Config(AppConfig):
    name = 'pqawV1'
    verbose_name = 'Probabilistic Question Asking - Web, Version 1'
    # https://stackoverflow.com/questions/6791911/execute-code-when-django-starts-once-only
    def ready(self):
        print('Startup of subsystems for PID=%s...' % (os.getpid(),))
        # input('Attach the debugger and press ENTER')
        # Init SRLogger
        probqa.SRLogger.init(os.path.join(settings.BASE_DIR, '../../logs/PqaWeb'))

        # TODO: take KB name from SQL DB
        engine, err = probqa.PqaEngineFactory.instance.load_cpu_engine(os.path.join(
            settings.BASE_DIR, '../../Data/KBs/current.kb'))
        if err:
            print('The engine is loaded nevertheless an error:', err.to_string(True))

        dims = engine.copy_dims()
        print('Total number of questions asked is %d. Engine dimensions are: %s.'
              % (engine.get_total_questions_asked(), dims))

        # Load ProbQA engine
        print('All subsystems operational!')
