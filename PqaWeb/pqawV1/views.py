from django.shortcuts import render
from django.http import HttpResponse, HttpRequest, Http404
from ProbQAInterop.ProbQA import PqaEngine, INVALID_PQA_ID
from .pivot import Pivot
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
            if quiz_comp_id == INVALID_PQA_ID:
                # No more in the engine - try to restore from session

                self.resume_quiz()
                return
            sel_action = self.request.POST.get('sel_action')
            if sel_action == 'StartNewQuiz':
                self.engine.release_quiz(quiz_comp_id)
                self.sess_hlp.deactivate_quiz(self.quiz_id)
                self.start_new_quiz()
                return
            if sel_action == 'RecordAnswer':
                option_pos = silent_int(self.request.POST.get('sel_param0'))
                # self.record_answer()
        elif self.request.method == 'GET':
            self.start_new_quiz()
        else:
            raise Http404('<h1>Unsupported request method %s</h1>' % self.request.method)


def index(request: HttpRequest):
    with Pivot.instance.lock_read() as lr:
        engine = Pivot.instance.get_engine()
        if not engine:
            lr.early_release()
            return HttpResponse('<h1>Maintenance is in progress.</h1>')
        qp = QuizPage(request, engine)
        qp.compute()
    return render(request, 'pqawV1/index.html', qp.context)
