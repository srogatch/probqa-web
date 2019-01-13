from django.http import HttpRequest
from ipware import get_client_ip
from ProbQAInterop.ProbQA import INVALID_PQA_ID
from pqawV1.pivot import pivot_instance
from .session_helper import SessionKeys
from .models import Quiz, Question, QuizTarget
from .exceptions import PqawInternalError
from django.db.models.signals import pre_delete
from django.contrib.sessions.models import Session


class QuizRegistry:
    def __init__(self, request: HttpRequest):
        self.request = request

    def is_active_quiz(self, quiz_id: int) -> bool:
        quiz_set = self.request.session.get(SessionKeys.ACTIVE_QUIZZES.value)
        if not quiz_set:
            return False
        return quiz_id in quiz_set

    def add_active_quiz(self, quiz_perm_id: int, active_question_perm_id: int) -> Quiz:
        user_ip, ip_routable = get_client_ip(self.request)
        active_question = Question.objects.get(pqa_id=active_question_perm_id)
        quiz = Quiz(pqa_id=quiz_perm_id, user_ip=user_ip, active_question=active_question)
        quiz.save()  # Must throw if pqa_id is not unique in the DB
        quiz_set = self.request.session.get(SessionKeys.ACTIVE_QUIZZES.value)
        if quiz_set:
            if quiz_perm_id in quiz_set:
                raise PqawInternalError('permID=%d of a new quiz is already in the session.' % quiz_perm_id)
            quiz_set.add(quiz_perm_id)
            self.request.session.modified = True
        else:
            self.request.session[SessionKeys.ACTIVE_QUIZZES.value] = {quiz_perm_id}
        return quiz

    # Must not throw
    def deactivate_quiz(self, quiz_id: int) -> None:
        quiz_set = self.request.session.get(SessionKeys.ACTIVE_QUIZZES.value)
        if quiz_set:
            if quiz_id in quiz_set:
                quiz_set.remove(quiz_id)
                self.request.session.modified = True

    def get_quiz(self, quiz_perm_id) -> Quiz:
        # Let it throw if quiz_id is not found
        return Quiz.objects.get(pqa_id=quiz_perm_id)

    def remap_quiz(self, quiz: Quiz, new_quiz_id: int) -> None:
        # Let it throw if old_quiz_id is not found
        active_quizzes = self.request.session[SessionKeys.ACTIVE_QUIZZES.value]
        active_quizzes.pop(quiz.pqa_id)
        active_quizzes.add(new_quiz_id)
        self.request.session.modified = True
        quiz.pqa_id = new_quiz_id
        quiz.save()

    def update_quiz_targets(self, quiz: Quiz, i_perm_target:int) -> None:
        last_choice = quiz.quizchoice_set.order_by('-id').first()
        if last_choice:
            last_choice_id = last_choice.id
        else:
            last_choice_id = INVALID_PQA_ID
        quiz.quiztarget_set.add(QuizTarget(target_pqa_id=i_perm_target, last_choice_id=last_choice_id), bulk=False)

    @staticmethod
    def on_session_expires(sender, **kwargs) -> None:
        session = kwargs.get('instance').get_decoded()
        print('Expiring session: %s' % session)
        quiz_set = session.get(SessionKeys.ACTIVE_QUIZZES.value)
        if quiz_set is None:
            return
        with pivot_instance.lock_shared():
            engine = pivot_instance.get_engine()
            if not engine:
                return
            quiz_comp_ids = engine.quiz_comp_from_perm(list(quiz_set))
            for qci in quiz_comp_ids:
                if qci != INVALID_PQA_ID:
                    engine.release_quiz(qci)

    @staticmethod
    def attach_session_expiration_handler():
        # https://stackoverflow.com/questions/4083426/django-detect-session-start-and-end
        pre_delete.connect(QuizRegistry.on_session_expires, sender=Session)
