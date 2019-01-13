import os
from django.conf import settings
import ProbQAInterop.ProbQA as probqa
from .models import KnowledgeBase, Quiz
from readerwriterlock import rwlock


class EarlyReleaseRWL:
    def __init__(self, a_rwlock):
        self.rwlock = a_rwlock

    def __enter__(self):
        self.rwlock.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.rwlock.locked():
            self.rwlock.release()

    def early_release(self):
        self.rwlock.release()


class Pivot:
    def __init__(self):
        self.engine = None
        self.main_lock = rwlock.RWLockWrite()
        self.per_tasks = None

    def lock_shared(self) -> EarlyReleaseRWL:
        return EarlyReleaseRWL(self.main_lock.gen_rlock())

    def lock_exclusive(self) -> EarlyReleaseRWL:
        return EarlyReleaseRWL(self.main_lock.gen_wlock())

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
        latest_kb_path = Pivot.get_latest_kb_path()
        if latest_kb_path:
            self.engine, err = probqa.pqa_engine_factory_instance.load_cpu_engine(latest_kb_path)
            if err:
                print('The engine is loaded nevertheless an error:', err.to_string(True))
            dims = self.engine.copy_dims()
            print('Total number of questions asked is %d. Engine dimensions are: %s.'
                  % (self.engine.get_total_questions_asked(), dims))
            last_quiz = Quiz.objects.order_by('-pqa_id').first()
            if last_quiz:
                self.engine.ensure_perm_quiz_greater(last_quiz.pqa_id)
            return True
        else:
            print('No knowledge base references found in the SQL database.')
            return False

    @staticmethod
    def get_latest_kb() -> KnowledgeBase:
        return KnowledgeBase.objects.order_by('-timestamp').first()

    @staticmethod
    def get_latest_kb_path() -> str:
        latest_kb = Pivot.get_latest_kb()
        if latest_kb is None:
            return None
        return os.path.join(settings.KB_ROOT, latest_kb.path)

    def init_periodic_tasks(self):
        from .periodic_tasks import PeriodicTasks
        self.per_tasks = PeriodicTasks()


pivot_instance = Pivot()
