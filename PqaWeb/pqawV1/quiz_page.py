import traceback

from django.http import HttpRequest, Http404
from django.conf import settings
from django.shortcuts import get_object_or_404

from ProbQAInterop.ProbQA import PqaEngine, INVALID_PQA_ID, AnsweredQuestion, PqaException
from .models import Question, QuizChoice, Target
from .utils import silent_int
from .quiz_registry import QuizRegistry


class TargetView:
    def __init__(self, link: str, title: str, perm_id: int, probability: float):
        self.link = link
        self.title = title
        self.perm_id = perm_id
        self.probability = probability


class QuizPage:
    def __init__(self, request: HttpRequest, engine: PqaEngine):
        self.request = request
        self.engine = engine
        self.context = {}
        self.quiz_reg = QuizRegistry(request)
        self.quiz = None
        self.quiz_comp_id = None  # Compact ID

    def start_new_quiz(self):
        self.quiz_comp_id = self.engine.start_quiz()
        quiz_perm_id = self.engine.quiz_perm_from_comp([self.quiz_comp_id])[0]
        i_comp_question = self.engine.next_question(self.quiz_comp_id)
        i_perm_question = self.engine.question_perm_from_comp([i_comp_question])[0]
        self.quiz = self.quiz_reg.add_active_quiz(quiz_perm_id, i_perm_question)
        self.fill_context()

    def fill_context(self):
        assert self.quiz_comp_id is not None
        if self.quiz is None:
            # Save a DB hit by not fetching the quiz
            i_comp_next_question = self.engine.get_active_question_id(self.quiz_comp_id)
            i_perm_next_question = self.engine.question_perm_from_comp([i_comp_next_question])[0]
            question = get_object_or_404(Question, pqa_id=i_perm_next_question)
            self.context['cur_quiz_id'] = self.engine.quiz_perm_from_comp([self.quiz_comp_id])[0]
        else:
            #TODO: verify the code below in debugger
            question = self.quiz.active_question
            self.context['cur_quiz_id'] = self.quiz.pqa_id
        self.context['question'] = question
        if question:
            self.context['answers'] = question.answer_set.order_by('option_pos')
            self.context['cur_question_id'] = question.pqa_id
        else:
            self.context['cur_question_id'] = INVALID_PQA_ID
        top_targets = self.engine.list_top_targets(self.quiz_comp_id, settings.PQA_TOP_TARGETS)
        i_perm_targets = self.engine.target_perm_from_comp([tt.i_target for tt in top_targets])
        db_targets = Target.objects.filter(pqa_id__in=i_perm_targets)
        dbt_refs = {dbt.pqa_id: dbt for dbt in db_targets}
        self.context['targets'] = [
            TargetView(dbt_refs[target_perm_id].link, dbt_refs[target_perm_id].title, target_perm_id,
                       rated_target.prob * 100)
            for target_perm_id, rated_target in zip(i_perm_targets, top_targets)]

    # Returns the compact ID for the next question
    def next_question_update_quiz(self) -> int:
        i_comp_active_question = INVALID_PQA_ID
        try:
            i_comp_active_question = self.engine.next_question(self.quiz_comp_id)
            active_question_perm_id = self.engine.question_perm_from_comp([i_comp_active_question])[0]
            self.quiz.active_question = Question.objects.get(pqa_id=active_question_perm_id)
        except PqaException:
            self.quiz.active_question = None
        self.quiz.save()
        return i_comp_active_question

    def compute(self) -> None:
        if self.request.method == 'POST':
            # Continue quiz, if it's valid
            quiz_perm_id = silent_int(self.request.POST.get('cur_quiz_id'))
            if quiz_perm_id is None:
                self.start_new_quiz()
                return
            if not self.quiz_reg.is_active_quiz(quiz_perm_id):
                # Assume the session has expired or the user forges someone else's quiz ID
                self.start_new_quiz()
                return
            # By now we are sure that this quiz belongs to this user: we can continue it or release it, etc.
            self.quiz_comp_id = self.engine.quiz_comp_from_perm([quiz_perm_id])[0]
            sel_action = self.request.POST.get('sel_action')
            sel_param0 = self.request.POST.get('sel_param0')
            if sel_action == 'StartNewQuiz':
                self.quiz_reg.deactivate_quiz(quiz_perm_id)
                # If the above throws, then the quiz leaks in the engine
                if self.quiz_comp_id != INVALID_PQA_ID:
                    self.engine.release_quiz(self.quiz_comp_id)
                self.start_new_quiz()
                return
            if self.quiz_comp_id == INVALID_PQA_ID:
                # The quiz is no more in the engine. Try to restore from SQL DB.
                try:
                    self.quiz = self.quiz_reg.get_quiz(quiz_perm_id)
                except:
                    print('Quiz permID=%d is present in session, but not in SQL DB: %s'
                          % (quiz_perm_id, traceback.format_exc()))
                    # But let the user start a new quiz rather than see a strange error
                    self.start_new_quiz()
                    return
                # Answered Questions (aqs) with permanent IDs
                quiz_choices = self.quiz.quizchoice_set.all()
                # Compact question IDs
                comp_qids = self.engine.question_comp_from_perm([qc.question_pqa_id for qc in quiz_choices])
                # Answered Questions (aqs) with compact IDs.
                # Skip answered questions which are no more available in the engine.
                aqs_comp = [AnsweredQuestion(cqid, qc.i_answer)
                            for qc, cqid in zip(quiz_choices, comp_qids) if cqid != INVALID_PQA_ID]
                self.quiz_comp_id = self.engine.resume_quiz(aqs_comp)
                new_quiz_perm_id = self.engine.quiz_perm_from_comp([self.quiz_comp_id])[0]
                if not self.engine.remap_quiz_perm_id(new_quiz_perm_id, self.quiz.pqa_id, throw=False):
                    self.quiz_reg.remap_quiz(self.quiz, new_quiz_perm_id)

                active_question = self.quiz.active_question
                if active_question is None:
                    i_comp_active_question = INVALID_PQA_ID
                else:
                    i_comp_active_question = self.engine.question_comp_from_perm([active_question.pqa_id])[0]
                if i_comp_active_question == INVALID_PQA_ID:
                    self.next_question_update_quiz()
                    if sel_action == 'RecordTarget':
                        i_perm_target = silent_int(sel_param0)
                        if i_perm_target is not None:
                            i_comp_target = self.engine.target_comp_from_perm([i_perm_target])[0]
                            if i_comp_target == INVALID_PQA_ID:
                                print('While resuming quiz [%d], cannot record target with permanent ID=[%d] because it'
                                      ' has been deleted from the KB.' % (quiz_perm_id, i_perm_target))
                            else:
                                self.engine.record_quiz_target(self.quiz_comp_id, i_comp_target)
                                self.quiz_reg.update_quiz_targets(self.quiz, i_perm_target)
                    else:
                        print('While resuming quiz [%d], discard action [%s(%s)] because question [%s] has been deleted'
                              ' from the KB/DB.' % (quiz_perm_id, sel_action, sel_param0, str(active_question)))
                    self.fill_context()
                    return
                self.engine.set_active_question(self.quiz_comp_id, i_comp_active_question)
                # Fall through: we have resumed the quiz and ready to process the user action
            if sel_action == 'RecordAnswer':
                option_pos = silent_int(sel_param0)
                if (option_pos is None) or (option_pos not in range(settings.PQA_N_ANSWERS)):
                    raise Http404('Answer option position is out of range: ' + str(option_pos))
                if not self.quiz:
                    self.quiz = self.quiz_reg.get_quiz(quiz_perm_id)
                i_comp_active_question = self.engine.get_active_question_id(self.quiz_comp_id)
                if (i_comp_active_question == INVALID_PQA_ID) or (self.quiz.active_question is None):
                    # No more questions to ask
                    assert (i_comp_active_question == INVALID_PQA_ID) and (self.quiz.active_question is None)
                else:
                    i_perm_active_question = self.engine.question_perm_from_comp([i_comp_active_question])[0]
                    assert self.quiz.active_question.pqa_id == i_perm_active_question
                    page_active_question = silent_int(self.request.POST.get('cur_question_id'))
                    # It may be unequal if user presses "Refresh" on the page and resubmits the form.
                    if page_active_question == i_perm_active_question:
                        self.engine.record_answer(self.quiz_comp_id, option_pos)
                        self.quiz.quizchoice_set.add(QuizChoice(question_pqa_id=self.quiz.active_question.pqa_id,
                                                                i_answer=option_pos), bulk=False)
                        self.next_question_update_quiz()
            elif sel_action == 'RecordTarget':
                i_perm_target = silent_int(sel_param0)
                if i_perm_target is not None:
                    i_comp_target = self.engine.target_comp_from_perm([i_perm_target])[0]
                    if i_comp_target != INVALID_PQA_ID:
                        self.engine.record_quiz_target(self.quiz_comp_id, i_comp_target)
                        self.quiz = self.quiz_reg.get_quiz(quiz_perm_id)
                        self.quiz_reg.update_quiz_targets(self.quiz, i_perm_target)
                # Note that self.quiz may be None here, so fill_context() should check for this case
            else:
                raise Http404('Unsupported here action: [%s(%s)]' % (sel_action, sel_param0))
            self.fill_context()
            return
        elif self.request.method == 'GET':
            self.start_new_quiz()
            return
        else:
            raise Http404('Unsupported request method: [%s]' % self.request.method)
