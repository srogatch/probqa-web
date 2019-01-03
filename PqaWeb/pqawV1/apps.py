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
        # Test creation of the engine
        engine, err = probqa.PqaEngineFactory.instance.create_cpu_engine(probqa.EngineDefinition(
            n_answers = 5, # Use 0 or 1 to trigger an error
            n_questions = 10,
            n_targets = 10,
        ))
        if err:
            print(err.to_string(True))
        if not engine:
            print('Got no engine')
            return # Actually, stop the program if we can't create an engine
        comp_ids = list(range(2, 10, 2))
        print('Compact IDs:', comp_ids)
        perm_ids = engine.question_perm_from_comp(comp_ids)
        print('Permanent IDs:', perm_ids)

        engine, err = probqa.PqaEngineFactory.instance.load_cpu_engine(os.path.join(
            settings.BASE_DIR, '../../Data/KBs/current.kb'))
        if err:
            print(err.to_string(True))
        if not engine:
            print('Loaded no engine')
            return # Actually, stop the program if we can't create an engine

        # Load ProbQA engine
        print('All subsystems operational!')
