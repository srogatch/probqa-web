from django.http import HttpRequest, Http404
from django.conf import settings
from django.shortcuts import get_object_or_404

from ProbQAInterop.ProbQA import PqaEngine, INVALID_PQA_ID, AnsweredQuestion
from .models import Question
from .session_helper import SessionHelper
from .utils import silent_int


class QuizPage:
    def __init__(self, request: HttpRequest, engine: PqaEngine):
        self.request = request
        self.engine = engine
        self.context = {}
        self.sess_hlp = SessionHelper(request)
        self.quiz_id = None  # Permanent ID
        self.quiz_info = None
        self.quiz_comp_id = None  # Compact ID

    def start_new_quiz(self):
        self.quiz_comp_id = self.engine.start_quiz()
        self.quiz_id = self.engine.quiz_perm_from_comp([self.quiz_comp_id])[0]
        self.quiz_info = self.sess_hlp.add_active_quiz(self.quiz_id)
        i_comp_question = self.engine.next_question(self.quiz_comp_id)
        i_perm_question = self.engine.question_perm_from_comp([i_comp_question])[0]
        self.quiz_info.i_active_question = i_perm_question
        self.sess_hlp.mark_modified()
        self.fill_context()

    def fill_context(self):
        assert self.quiz_id is not None
        assert self.quiz_comp_id is not None
        if self.quiz_info is None:
            i_comp_next_question = self.engine.get_active_question_id(self.quiz_comp_id)
            i_perm_next_question = self.engine.question_perm_from_comp([i_comp_next_question])[0]
        else:
            i_perm_next_question = self.quiz_info.i_active_question
        self.context['question'] = get_object_or_404(Question, pqa_id=i_perm_next_question)
        self.context['cur_quiz_id'] = self.quiz_id

    def compute(self) -> None:
        if self.request.method == 'POST':
            # Continue quiz, if it's valid
            self.quiz_id = silent_int(self.request.POST.get('cur_quiz_id'))
            if self.quiz_id is None:
                self.start_new_quiz()
                return
            if not self.sess_hlp.is_active_quiz(self.quiz_id):
                # Assume the session has expired
                self.start_new_quiz()
                return
            self.quiz_comp_id = self.engine.quiz_comp_from_perm([self.quiz_id])[0]
            sel_action = self.request.POST.get('sel_action')
            sel_param0 = self.request.POST.get('sel_param0')
            if sel_action == 'StartNewQuiz':
                self.sess_hlp.deactivate_quiz(self.quiz_id)
                # If the above throws, then the quiz leaks in the engine
                if self.quiz_comp_id != INVALID_PQA_ID:
                    self.engine.release_quiz(self.quiz_comp_id)
                self.start_new_quiz()
                return
            if self.quiz_comp_id == INVALID_PQA_ID:
                # No more in the engine - try to restore from session.
                # Answered Questions (aqs) with permanent IDs
                self.quiz_info = self.sess_hlp.get_quiz_info(self.quiz_id)
                aqs_perm = self.quiz_info.sequence
                # Compact question IDs
                comp_qids = self.engine.question_comp_from_perm([aq.i_question for aq in aqs_perm])
                # Answered Questions (aqs) with compact IDs.
                # Skip answered questions which are no more available in the engine.
                aqs_comp = [AnsweredQuestion(cqid, aqp.i_answer)
                            for aqp, cqid in zip(aqs_perm, comp_qids) if cqid != INVALID_PQA_ID]
                self.quiz_comp_id = self.engine.resume_quiz(aqs_comp)
                old_quiz_id = self.quiz_id
                self.quiz_id = self.engine.quiz_perm_from_comp([self.quiz_comp_id])[0]
                self.sess_hlp.remap_quiz(old_quiz_id, self.quiz_id)
                i_comp_active_question = self.engine.question_comp_from_perm([self.quiz_info.i_active_question])[0]
                if i_comp_active_question == INVALID_PQA_ID:
                    i_comp_active_question = self.engine.next_question(self.quiz_comp_id)
                    old_active_question = self.quiz_info.i_active_question
                    self.quiz_info.i_active_question = self.engine.question_perm_from_comp([i_comp_active_question])[0]
                    self.sess_hlp.mark_modified()
                    if sel_action == 'RecordTarget':
                        i_perm_target = silent_int(sel_param0)
                        if i_perm_target is not None:
                            i_comp_target = self.engine.target_comp_from_perm([i_perm_target])[0]
                            if i_comp_target == INVALID_PQA_ID:
                                print('While resuming quiz [%d], cannot record target with permanent ID=[%d] because it'
                                      ' has been deleted from the KB.' % (self.quiz_id, i_perm_target))
                            else:
                                self.engine.record_quiz_target(self.quiz_comp_id, i_comp_target)
                    else:
                        print('While resuming quiz [%d], discard action [%s(%s)] because question with permanent'
                              ' ID=[%d] has been deleted from the KB.'
                              % (self.quiz_id, sel_action, sel_param0, old_active_question))
                    self.fill_context()
                    return
                self.engine.set_active_question(self.quiz_comp_id, i_comp_active_question)
                # Fall through: we have resumed the quiz and ready to process the user action
            if sel_action == 'RecordAnswer':
                option_pos = silent_int(sel_param0)
                if (option_pos is None) or (option_pos not in range(settings.PQA_N_ANSWERS)):
                    raise Http404('Answer option position is out of range: ' + str(option_pos))
                self.quiz_info = self.sess_hlp.get_quiz_info(self.quiz_id)
                # TODO: remove self-verification after the program is stable
                # Self-verification code start
                i_comp_active_question = self.engine.get_active_question_id(self.quiz_comp_id)
                i_perm_active_question = self.engine.question_perm_from_comp([i_comp_active_question])[0]
                assert self.quiz_info.i_active_question == i_perm_active_question
                # Self-verification code end
                self.engine.record_answer(self.quiz_comp_id, option_pos)
                self.quiz_info.sequence.append(AnsweredQuestion(i_perm_active_question, option_pos))
                self.sess_hlp.mark_modified()  # Persist if an exception is thrown below
                i_comp_next_question = self.engine.next_question(self.quiz_comp_id)
                i_perm_next_question = self.engine.question_perm_from_comp([i_comp_next_question])
                self.quiz_info.i_active_question = i_perm_next_question
            elif sel_action == 'RecordTarget':
                i_perm_target = silent_int(sel_param0)
                if i_perm_target is not None:
                    i_comp_target = self.engine.target_comp_from_perm([i_perm_target])[0]
                    if i_comp_target != INVALID_PQA_ID:
                        self.engine.record_quiz_target(self.quiz_comp_id, i_comp_target)
                # Note that self.quiz_info may be None here, so fill_context() should check for this case
            else:
                raise Http404('Unsupported here action: [%s(%s)]' % (sel_action, sel_param0))
            self.fill_context()
            return
        elif self.request.method == 'GET':
            self.start_new_quiz()
            return
        else:
            raise Http404('Unsupported request method: [%s]' % self.request.method)
