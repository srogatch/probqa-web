import time
import traceback
from threading import Thread

from pqawV1.admin_actions import AdminActions
from .pivot import pivot_instance
from datetime import datetime
from django.conf import settings


class PeriodicTasks:
    def __init__(self):
        very_old_dt = datetime.fromtimestamp(0)
        dt_now = datetime.utcnow()
        self.last_clear_old_quizzes = dt_now
        self.last_save_engine = dt_now
        self.thr = Thread(target=self.async_run, name='Periodic tasks')
        self.thr.daemon = True
        self.thr.start()

    def async_run(self):
        while True:
            dt_now = datetime.utcnow()
            if (dt_now - self.last_clear_old_quizzes).total_seconds() > settings.CLEAR_OLD_QUIZZES_CHECK_PERIOD_SEC:
                self.last_clear_old_quizzes = dt_now
                with pivot_instance.lock_exclusive():
                    engine = pivot_instance.get_engine()
                    if engine is not None:
                        try:
                            engine.clear_old_quizzes(settings.CLEAR_QUIZZES_IF_COUNT_EXCEEDS,
                                                     settings.CLEAR_QUIZZES_AGE_SEC)
                        except:
                            print(traceback.format_exc())
            #TODO: save engine periodically
            if(dt_now - self.last_save_engine).total_seconds() > settings.SAVE_ENGINE_PERIOD_SEC:
                self.last_save_engine = dt_now
                aa = AdminActions()
                aa.save_engine()
            time.sleep(1)
