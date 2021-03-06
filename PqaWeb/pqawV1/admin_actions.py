import datetime
import os
import traceback
from threading import Thread

from typing import Union, List
from django.db.models import QuerySet
from django.conf import settings
from django.db import transaction

from ThirdParty.DjangoArchive.backupper import Backupper

from ProbQAInterop.ProbQA import EngineDefinition, AddQuestionParam, AddTargetParam, pqa_engine_factory_instance
from pqawV1.pivot import pivot_instance
from .models import *


class SksException(Exception):
    pass


class AdminActions:
    def __init__(self):
        self.engine = None
        self.utc_now = datetime.datetime.utcnow()
        self.timestamp_file_name = self.utc_now.strftime('%Y-%m-%d_%H-%M-%S_%f')
        self.new_kb_file_name = self.timestamp_file_name + '.kb'
        self.goal_kb_path = os.path.join(settings.KB_ROOT, self.new_kb_file_name)
        self.res_msg = None  # Result message for the admin

    @staticmethod
    def validate_answers(questions: Union[QuerySet, List[Question]]) -> None:
        all_answers = Answer.objects.filter(question__in=questions)
        q2as = dict()
        for a in all_answers:
            q_id = a.question.id
            if q_id in q2as:
                q2as[q_id].append(a.option_pos)
            else:
                q2as[q_id] = [a.option_pos]
        for q_id in q2as:
            if sorted(q2as[q_id]) != list(range(settings.PQA_N_ANSWERS)):
                raise SksException('Invalid answer options detected for question: '
                                   + str(Question.objects.get(id=q_id)))


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
            AdminActions.validate_answers(questions)

            targets = Target.objects.only('id', 'pqa_id', 'retain')
            targets.filter(retain=False).delete()
            n_targets = len(targets)
            if n_targets < settings.PQA_MIN_TARGETS:
                # Raise an exception to rollback the transaction
                raise SksException('At least %d targets are required to launch an engine, but found only %d in the DB'
                    % (settings.PQA_MIN_TARGETS, n_targets))

            ed = EngineDefinition(settings.PQA_N_ANSWERS, n_questions, n_targets)
            self.engine, err = pqa_engine_factory_instance.create_cpu_engine(ed)
            if err:
                print('An engine is created nevertheless an error:', str(err))
            perm_question_ids = self.engine.question_perm_from_comp(list(range(n_questions)))
            perm_target_ids = self.engine.target_perm_from_comp(list(range(n_targets)))
            i = 0
            for q in questions:
                if q.pqa_id is not None:
                    raise SksException('pqa_id=%d is assigned to a question - there is a risk we are overwriting an'
                                       ' existing engine!' % q.pqa_id)
                q.pqa_id = perm_question_ids[i]
                i += 1
            i = 0
            for t in targets:
                if t.pqa_id is not None:
                    raise SksException('pqa_id=%d is assigned to a target - there is a risk we are overwriting an'
                                       ' existing engine!' % t.pqa_id)
                t.pqa_id = perm_target_ids[i]
                i += 1
            # Below is a very slow way to do this, but there doesn't seem to be something better in Django ORM
            for q in questions:
                q.save()
            for t in targets:
                t.save()
            self.engine.save_kb(self.goal_kb_path, False)
            KnowledgeBase(path=self.new_kb_file_name).save()
        pivot_instance.set_engine(self.engine)
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
                del_questions.delete()
                add_questions_db = questions.filter(pqa_id=None)
                AdminActions.validate_answers(add_questions_db)

                targets = Target.objects.only('id', 'pqa_id', 'retain')
                del_targets = targets.filter(retain=False)
                perm_del_tas = [t.pqa_id for t in del_targets if t.pqa_id is not None]
                comp_del_tas = self.engine.target_comp_from_perm(perm_del_tas)
                self.engine.remove_targets(comp_del_tas)
                del_targets.delete()
                add_targets_db = targets.filter(pqa_id=None)

                add_question_params = [AddQuestionParam() for _ in range(len(add_questions_db))]
                add_target_params = [AddTargetParam() for _ in range(len(add_targets_db))]
                self.engine.add_qs_ts(add_question_params, add_target_params)

                comp_new_qus = [aqp.i_question for aqp in add_question_params]
                perm_new_qus = self.engine.question_perm_from_comp(comp_new_qus)
                comp_new_tas = [atp.i_target for atp in add_target_params]
                perm_new_tas = self.engine.target_perm_from_comp(comp_new_tas)

                for aqdb, perm_qid in zip(add_questions_db, perm_new_qus):
                    aqdb.pqa_id = perm_qid
                for atdb, perm_tid in zip(add_targets_db, perm_new_tas):
                    atdb.pqa_id = perm_tid

                # Below is a very slow way to do this, but there doesn't seem to be something better in Django ORM
                for q in add_questions_db:
                    q.save()
                for t in add_targets_db:
                    t.save()

                # It returns the remapping of compact IDs that we don't need because we use permanent IDs
                self.engine.compact()

                self.engine.save_kb(self.goal_kb_path, False)
                KnowledgeBase(path=self.new_kb_file_name).save()
                # In the end, get the engine out of maintenance, however, still if this fails then we have to rollback
                #   SQL DB and restore the engine from backup.
                self.engine.finish_maintenance()
        except:
            exc_chain = traceback.format_exc()
            self.engine.shutdown(self.goal_kb_path + '.broken')  # This engine is broken
            try:
                # If the below raises, then we are left with an engine that is shut down
                self.engine, err = pqa_engine_factory_instance.load_cpu_engine(self.goal_kb_path + '.before')
                if err:
                    print('Backup engine is loaded nevertheless an error:', str(err))
                pivot_instance.set_engine(self.engine)
            except:
                exc_chain = traceback.format_exc() + '\n when handling \n' + exc_chain
                # Restore to even older version of the engine - which is referenced by the DB
                try:
                    pivot_instance.reset_engine()
                    self.engine = pivot_instance.get_engine()
                except:
                    exc_chain = traceback.format_exc() + '\n when handling \n' + exc_chain
                    raise SksException('Failed even to reset engine: \n\n' + exc_chain)
                raise SksException('Engine is reset after: \n\n' + exc_chain)
            raise SksException('Engine is restored from backup after: \n\n' + exc_chain)
        self.res_msg = 'Existing engine has been synchronized with SQL DB'

    def sync_sql_kb(self):
        try:
            with pivot_instance.lock_exclusive():
                self.engine = pivot_instance.get_engine()
                if self.engine:
                    self.use_existing_engine()
                    return
                # Load engine referenced by the KB
                if pivot_instance.reset_engine():
                    self.engine = pivot_instance.get_engine()
                    self.use_existing_engine()
                    return
                self.maybe_create_engine()
        except:
            self.res_msg = traceback.format_exc()

    def save_engine(self) -> bool:
        with pivot_instance.lock_shared():
            self.engine = pivot_instance.get_engine()
            if not self.engine:
                return False
            self.engine.save_kb(self.goal_kb_path, False)
            KnowledgeBase(path=self.new_kb_file_name).save()
        return True

    @staticmethod
    def format_engine_save_status(engine_saved: bool) -> str:
        if engine_saved:
            return 'ProbQA KB has been saved.'
        else:
            return 'No engine to save.'

    def async_backup_all(self):
        bu = Backupper(self.timestamp_file_name)
        with bu.create_archive() as tar:
            with pivot_instance.lock_shared():
                latest_kb_path = pivot_instance.get_latest_kb_path()
                bu.dump_sql_db(tar)
                bu.dump_media(tar)
            # Add the engine to the archive
            if latest_kb_path:
                tar.add(latest_kb_path, os.path.relpath(latest_kb_path, settings.KB_ROOT))
            else:
                print('No engine to backup.')
            bu.dump_meta(tar)
        print('BACKUP ALL: completed successfully!')

    def start_backup_all(self):
        engine_saved = self.save_engine()
        t = Thread(target=self.async_backup_all, name='Backupper')
        t.start()
        self.res_msg = AdminActions.format_engine_save_status(engine_saved)
        self.res_msg += (' A backup of SQL DB and media files, as well as archiving of the engine, have been launched'
                         ' asynchronously. See the console output for results\n')
