import os
import traceback
from django.conf import settings
import ProbQAInterop.ProbQA as probqa
from .models import KnowledgeBase

class Pivot:
    instance = None

    def __init__(self):
        self.engine = None

    def set_engine(self, engine: probqa.PqaEngine):
        self.engine = engine

    def get_engine(self) -> probqa.PqaEngine:
        return self.engine

    # If this function fails (i.e. with an exception), then the application shouldn't be run, otherwise it may happen
    #   during SQL-KB sync that we create a new engine nevertheless an engine is referenced in SQL database
    def reset_engine(self) -> bool:
        # If something later raises, keep no engine active
        self.engine = None
        # Take KB name from SQL DB
        latest_kb = KnowledgeBase.objects.order_by('-timestamp').first()
        if latest_kb:
            self.engine, err = probqa.PqaEngineFactory.instance.load_cpu_engine(os.path.join(
                settings.KB_ROOT, latest_kb.path))
            if err:
                print('The engine is loaded nevertheless an error:', err.to_string(True))
            dims = self.engine.copy_dims()
            print('Total number of questions asked is %d. Engine dimensions are: %s.'
                  % (self.engine.get_total_questions_asked(), dims))
            return True
        else:
            print('No knowledge base references found in the SQL database.')
            return False


Pivot.instance = Pivot()
