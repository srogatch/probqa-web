from typing import List

from django.contrib.sessions.backends.base import SessionBase
from enum import Enum
from django.http import HttpRequest
from ProbQAInterop.ProbQA import AnsweredQuestion, INVALID_PQA_ID


class Keys(Enum):
    QUIZ_INFOS = 'quiz_infos'


class QuizInfo:
    def __init__(self):
        self.i_active_question = INVALID_PQA_ID
        self.sequence = []


class SessionHelper:
    def __init__(self, request: HttpRequest):
        self.request = request

    def is_active_quiz(self, quiz_id: int) -> bool:
        mappings = self.request.session[Keys.QUIZ_INFOS]
        if not mappings:
            return False
        return quiz_id in mappings

    def add_active_quiz(self, quiz_id: int) -> None:
        mappings = self.request.session[Keys.QUIZ_INFOS]
        if mappings:
            self.request.session[Keys.QUIZ_INFOS][quiz_id] = QuizInfo()
            self.request.session.modified = True
        else:
            self.request.session[Keys.QUIZ_INFOS] = {quiz_id: QuizInfo()}

    def deactivate_quiz(self, quiz_id: int) -> None:
        mappings = self.request.session[Keys.QUIZ_INFOS]
        if mappings:
            if quiz_id in mappings:
                mappings.remove(quiz_id)
                self.request.session.modified = True

    # Note that |aq| here must contain permanent ID
    def add_to_quiz_sequence(self, quiz_id: int, aq: AnsweredQuestion) -> None:
        # Let it throw if quiz_id is not among the active quizzes
        self.request.session[Keys.QUIZ_INFOS][quiz_id].sequence.append(aq)
        self.request.session.modified = True

    def get_quiz_info(self, quiz_id) -> QuizInfo:
        # Let it throw if quiz_id is not found
        return self.request.session[Keys.QUIZ_INFOS][quiz_id]

    def remap_quiz(self, old_quiz_id: int, new_quiz_id: int) -> None:
        # Let it throw if old_quiz_id is not found
        info = self.request.session[Keys.QUIZ_INFOS].pop(old_quiz_id)
        self.request.session[Keys.QUIZ_INFOS][new_quiz_id] = info
        self.request.session.modified = True
