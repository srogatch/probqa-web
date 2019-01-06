from .pivot import Pivot
from .models import *
import datetime
import os
from django.conf import settings
from ProbQAInterop.ProbQA import MaintenanceLock, PqaEngineFactory, EngineDefinition
from django.db import transaction
import traceback

class SksException(Exception):
    pass

class SqlKbSync:
    def __init__(self):
        self.engine = Pivot.instance.get_engine()
        self.utc_now = datetime.datetime.utcnow()
        self.new_kb_file_name = self.utc_now.strftime('%Y-%m-%d_%H-%M-%S_%f.kb')
        self.res_msg = None  # Result message for the admin

    # Maybe create an engine if SQL DB contains enough data
    def maybe_create_engine(self):
        with transaction.atomic():
            questions = Question.objects.only('id', 'pqa_id', 'retain')
            questions.filter(retain=False).delete()
            n_questions = len(questions)
            if n_questions < settings.PQA_MIN_QUESTIONS:
                # Raise an exception to rollback the transaction
                raise SksException('At least %d questions are required to launch an engine, but found only %d in the DB'
                    % (settings.PQA_MIN_QUESTIONS, n_questions))
            targets = Target.objects.only('id', 'pqa_id', 'retain')
            targets.filter(retain=False).delete()
            n_targets = len(targets)
            if n_targets < settings.PQA_MIN_TARGETS:
                # Raise an exception to rollback the transaction
                raise SksException('At least %d targets are required to launch an engine, but found only %d in the DB'
                    % (settings.PQA_MIN_TARGETS, n_targets))
            ed = EngineDefinition(settings.PQA_N_ANSWERS, n_questions, n_targets)
            self.engine, err = PqaEngineFactory.instance.create_cpu_engine(ed)
            if err:
                print('An engine is created nevertheless an error:', )
            perm_question_ids = self.engine.question_perm_from_comp(list(range(n_questions)))
            perm_target_ids = self.engine.target_perm_from_comp(list(range(n_targets)))
            i = 0
            for q in questions:
                q.pqa_id = perm_question_ids[i]
                i += 1
            i = 0
            for t in targets:
                t.pqa_id = perm_target_ids[i]
                i += 1
            for q in questions:
                q.save()
            for t in targets:
                t.save()
            KnowledgeBase(path=self.new_kb_file_name).save()
            self.engine.save_kb(os.path.join(settings.KB_ROOT, self.new_kb_file_name), False)
        Pivot.instance.set_engine(self.engine)
        self.res_msg = 'A new engine has been created'

    def use_existing_engine(self):
        with MaintenanceLock(self.engine, True):  # Force quizzes
            self.engine.save_kb(os.path.join(settings.KB_ROOT, self.new_kb_file_name), False)

    def go(self):
        try:
            if self.engine:
                self.use_existing_engine()
            else:
                self.maybe_create_engine()
        except Exception:
            self.res_msg = str(traceback.format_exc())
