from django.http import HttpRequest, Http404
from ProbQAInterop.ProbQA import PqaEngine, INVALID_PQA_ID, AnsweredQuestion
from .session_helper import SessionHelper
from .utils import silent_int


class QuizPage:
    def __init__(self, request: HttpRequest, engine: PqaEngine):
        self.request = request
        self.engine = engine
        self.context = {}
        self.sess_hlp = SessionHelper(request)
        self.quiz_id = None
        pass

    def start_new_quiz(self):
        pass

    def resume_quiz(self):
        pass

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
            quiz_comp_id = self.engine.quiz_comp_from_perm([self.quiz_id])[0]
            sel_action = self.request.POST.get('sel_action')
            if sel_action == 'StartNewQuiz':
                self.sess_hlp.deactivate_quiz(self.quiz_id)
                # If the above throws, then the quiz leaks in the engine
                if quiz_comp_id != INVALID_PQA_ID:
                    self.engine.release_quiz(quiz_comp_id)
                self.start_new_quiz()
                return
            if quiz_comp_id == INVALID_PQA_ID:
                # No more in the engine - try to restore from session.
                # Answered Questions (aqs) with permanent IDs
                quiz_info = self.sess_hlp.get_quiz_info(self.quiz_id)
                aqs_perm = quiz_info.sequence
                # Compact question IDs
                comp_qids = self.engine.question_comp_from_perm([aq.i_question for aq in aqs_perm])
                # Answered Questions (aqs) with compact IDs.
                # Skip answered questions which are no more available in the engine.
                aqs_comp = [AnsweredQuestion(cqid, aqp.i_answer)
                            for aqp, cqid in zip(aqs_perm, comp_qids) if cqid != INVALID_PQA_ID]
                quiz_comp_id = self.engine.resume_quiz(aqs_comp)
                old_quiz_id = self.quiz_id
                self.quiz_id = self.engine.quiz_perm_from_comp([quiz_comp_id])
                self.sess_hlp.remap_quiz(old_quiz_id, self.quiz_id)
                self.engine.set_active_question(quiz_comp_id, quiz_info.i_active_question)
                # Fall through: we have resumed the quiz and ready to process the user action
            if sel_action == 'RecordAnswer':
                option_pos = silent_int(self.request.POST.get('sel_param0'))
                # self.record_answer()
        elif self.request.method == 'GET':
            self.start_new_quiz()
            return
        else:
            raise Http404('<h1>Unsupported request method %s</h1>' % self.request.method)
