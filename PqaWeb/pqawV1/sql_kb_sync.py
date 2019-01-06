from .pivot import Pivot
from .models import *
import datetime
import os
import traceback
from django.conf import settings
from ProbQAInterop.ProbQA import PqaEngineFactory, EngineDefinition
from django.db import transaction

class SksException(Exception):
    pass

class SqlKbSync:
    def __init__(self):
        self.engine = Pivot.instance.get_engine()
        self.utc_now = datetime.datetime.utcnow()
        self.new_kb_file_name = self.utc_now.strftime('%Y-%m-%d_%H-%M-%S_%f.kb')
        self.goal_kb_path = os.path.join(settings.KB_ROOT, self.new_kb_file_name)
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
                print('An engine is created nevertheless an error:', str(err))
            perm_question_ids = self.engine.question_perm_from_comp(list(range(n_questions)))
            perm_target_ids = self.engine.target_perm_from_comp(list(range(n_targets)))
            i = 0
            for q in questions:
                if q.pqa_id is not None:
                    raise SksException('pqa_id=%d is assigned to a question - there is a risk we are overwriting an' +
                                       ' existing engine!' % (q.pqa_id,))
                q.pqa_id = perm_question_ids[i]
                i += 1
            i = 0
            for t in targets:
                if t.pqa_id is not None:
                    raise SksException('pqa_id=%d is assigned to a target - there is a risk we are overwriting an' +
                                       ' existing engine!' % (t.pqa_id,))
                t.pqa_id = perm_target_ids[i]
                i += 1
            # Below is a very slow way to do this, but there doesn't seem to be something better in Django ORM
            for q in questions:
                q.save()
            for t in targets:
                t.save()
            self.engine.save_kb(self.goal_kb_path, False)
            KnowledgeBase(path=self.new_kb_file_name).save()
        Pivot.instance.set_engine(self.engine)
        self.res_msg = 'A new engine has been created'

    def use_existing_engine(self):
        self.engine.start_maintenance(True)  # Force quizzes
        try:
            # Backup the KB before applying the heaviest stuff
            self.engine.save_kb(self.goal_kb_path + '.before', False)
        except:
            # If KB doesn't get backed up, then we don't proceed with the heaviest stuff
            self.engine.finish_maintenance()
            raise
        try:
            with transaction.atomic():
                questions = Question.objects.only('id', 'pqa_id', 'retain')
                del_questions = questions.filter(retain=False)
                perm_del_qus = [q.pqa_id for q in del_questions if q.pqa_id is not None]
                comp_del_qus = self.engine.question_comp_from_perm(perm_del_qus)
                self.engine.remove_questions(comp_del_qus)
                # In the end, get the engine out of maintenance, however, still if this fails then we have to rollback
                #   SQL DB and restore the engine from backup.
                # In multi-threaded environment there would be a chance that some user can connect in the moment between
                #   when engine accepts the requests, but database is not yet ready (the current transaction is not yet
                #   comitted). In this case the user gets nonsense responses from the website.
                self.engine.finish_maintenance()
        except:
            exc_chain = traceback.format_exc()
            self.engine.shutdown(self.goal_kb_path + '.broken')  # This engine is broken
            try:
                # If the below raises, then we are left with an engine that is shut down
                self.engine, err = PqaEngineFactory.instance.load_cpu_engine(self.goal_kb_path + '.before')
                if err:
                    print('Backup engine is loaded nevertheless an error:', str(err))
                Pivot.instance.set_engine(self.engine)
            except:
                exc_chain = traceback.format_exc() + '\n when handling \n' + exc_chain
                # Restore to even older version of the engine - which is referenced by the DB
                try:
                    Pivot.instance.reset_engine()
                except:
                    exc_chain = traceback.format_exc() + '\n when handling \n' + exc_chain
                    raise SksException('Failed even to reset engine: ' + exc_chain)
                raise SksException('Engine is reset after: ' + exc_chain)
            raise SksException('Engine is restored from backup after: ' + exc_chain)

    def go(self):
        try:
            if self.engine:
                self.use_existing_engine()
                return
            # Load engine referenced by the KB
            if Pivot.instance.reset_engine():
                self.engine = Pivot.instance.get_engine()
                self.use_existing_engine()
                return
            self.maybe_create_engine()
        except:
            self.res_msg = traceback.format_exc()
