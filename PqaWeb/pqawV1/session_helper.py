from django.contrib.sessions.backends.base import SessionBase
from enum import Enum
from django.http import HttpRequest
from ProbQAInterop.ProbQA import AnsweredQuestion


class Keys(Enum):
    ACTIVE_QUIZZES = 'active_quizzes'
    QUIZ_SEQUENCES = 'quiz_sequences'


class SessionHelper:
    def __init__(self, request: HttpRequest):
        self.request = request

    def is_active_quiz(self, quiz_id: int) -> bool:
        active_quizzes = self.request.session[Keys.ACTIVE_QUIZZES]
        if not active_quizzes:
            return False
        return quiz_id in active_quizzes

    def add_active_quiz(self, quiz_id: int) -> None:
        active_quizzes = self.request.session[Keys.ACTIVE_QUIZZES]
        if active_quizzes:
            active_quizzes.add(quiz_id)
            self.request.session.modified = True
        else:
            self.request.session[Keys.ACTIVE_QUIZZES] = { quiz_id }
        quiz_sequences = self.request.session[Keys.QUIZ_SEQUENCES]
        if quiz_sequences:
            self.request.session[Keys.QUIZ_SEQUENCES][quiz_id] = []
            self.request.session.modified = True
        else:
            self.request.session[Keys.QUIZ_SEQUENCES] = {quiz_id: []}

    def deactivate_quiz(self, quiz_id: int) -> None:
        active_quizzes = self.request.session[Keys.ACTIVE_QUIZZES]
        if active_quizzes:
            if quiz_id in active_quizzes:
                active_quizzes.remove(quiz_id)
        quiz_sequences = self.request.session[Keys.QUIZ_SEQUENCES]
        if quiz_sequences:
            if quiz_id in quiz_sequences:
                quiz_sequences.remove(quiz_id)
