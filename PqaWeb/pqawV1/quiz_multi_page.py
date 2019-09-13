import traceback

from django.http import HttpRequest, Http404
from django.conf import settings
from django.shortcuts import get_object_or_404

from ipware import get_client_ip

from ProbQAInterop.ProbQA import PqaEngine, INVALID_PQA_ID, AnsweredQuestion
from .models import Question, Target, Answer, UserTraining
from .utils import silent_int, format_probability
from .target_view import TargetView


class AnswerView:
    def __init__(self, ans : Answer, request: HttpRequest, ipq : int, iao : int):
        self.db_ans = ans
        updated = request.GET.copy()
        updated['q' + str(ipq)] = str(iao)
        self.query = updated.urlencode()


class QuizMultiPage:
    def __init__(self, request: HttpRequest, engine: PqaEngine):
        self.request = request
        self.engine = engine
        self.context = {}
        self.quiz_comp_id = None
        # https://bradmontgomery.net/blog/restricting-access-by-group-in-django/
        self.is_teacher = (request.user.groups.filter(name='Teaching').count() > 0)

    def fill_context(self):
        i_comp_next_question = self.engine.next_question(self.quiz_comp_id)
        if i_comp_next_question != INVALID_PQA_ID:
            i_perm_next_question = self.engine.question_perm_from_comp([i_comp_next_question])[0]
            question = get_object_or_404(Question, pqa_id=i_perm_next_question)
        else:
            question = None
        self.context['question'] = question
        if question:
            answers = question.answer_set.order_by('option_pos')
            avs = [AnswerView(ans, self.request, i_perm_next_question, ans.option_pos) for ans in answers]
            self.context['answers'] = avs

        self.context['is_teacher'] = self.is_teacher
        self.context['scroll_pos'] = self.request.POST.get('scroll_pos', 0)

        teaching_target_filter = self.request.POST.get('teaching_target_filter')
        if self.is_teacher and teaching_target_filter:
            dims = self.engine.copy_dims()
            all_targets = self.engine.list_top_targets(self.quiz_comp_id, dims.n_targets)
            i_perm_targets = self.engine.target_perm_from_comp([tt.i_target for tt in all_targets])
            permid2prob = {perm_id: tt.prob for perm_id, tt in zip(i_perm_targets, all_targets)}
            # This still performs a case-sensitive search in MySQL
            db_targets = Target.objects.filter(title__icontains=teaching_target_filter).filter(pqa_id__isnull=False)
            self.context['targets'] = [
                TargetView(dbt.link,
                           dbt.title,
                           dbt.pqa_id,
                           format_probability(permid2prob[dbt.pqa_id]),
                           dbt.description,
                           dbt.thumbnail.url)
                for dbt in db_targets]
        else:
            top_targets = self.engine.list_top_targets(self.quiz_comp_id, settings.PQA_TOP_TARGETS)
            i_perm_targets = self.engine.target_perm_from_comp([tt.i_target for tt in top_targets])
            db_targets = Target.objects.filter(pqa_id__in=i_perm_targets)
            dbt_refs = {dbt.pqa_id: dbt for dbt in db_targets}
            self.context['targets'] = [
                TargetView(dbt_refs[target_perm_id].link,
                           dbt_refs[target_perm_id].title,
                           target_perm_id,
                           format_probability(rated_target.prob),
                           dbt_refs[target_perm_id].description,
                           dbt_refs[target_perm_id].thumbnail.url)
                for target_perm_id, rated_target in zip(i_perm_targets, top_targets)]



    def compute(self):
        # Independently of the request method, parse the URL parameters so to restore the quiz
        url_params = self.request.GET.items()
        perm_question_ids = []
        answer_ids = []
        for k,v in url_params:
            if str(k).startswith('q'):
                try:
                    qid = int(k[1:])
                    aid = int(v)
                    perm_question_ids.append(qid)
                    answer_ids.append(aid)
                except:
                    pass;
        comp_question_ids = self.engine.question_comp_from_perm(perm_question_ids)
        aqs = [AnsweredQuestion(iq, ia) for iq, ia in zip(comp_question_ids, answer_ids)
               if iq != INVALID_PQA_ID]
        self.quiz_comp_id = self.engine.resume_quiz(aqs)

        if self.request.method == 'POST':
            sel_action = self.request.POST.get('sel_action')
            sel_param0 = self.request.POST.get('sel_param0')
            if sel_action == 'RecordTarget':
                i_perm_target = silent_int(sel_param0)
                if i_perm_target is not None:
                    i_comp_target = self.engine.target_comp_from_perm([i_perm_target])[0]
                    if i_comp_target != INVALID_PQA_ID:
                        user_ip, ip_routable = get_client_ip(self.request)
                        ut = UserTraining(user_ip=user_ip, username=self.request.user.username,
                            target_pqa_id=i_perm_target,
                            query_url=self.request.build_absolute_uri(self.request.get_full_path()))
                        ut.save()
                        self.engine.record_quiz_target(self.quiz_comp_id, i_comp_target)
                        # TODO: track in the DB the user who clicked this target for the quiz
            elif self.is_teacher: # Can click 'Submit' button
                pass
            else:
                raise Http404('Unsupported ProbQA action: [%s(%s)]' % (sel_action, sel_param0))
        elif self.request.method == 'GET' or self.request.method == 'HEAD':
            pass # Fall through
        else:
            raise Http404('Unsupported request method: [%s]' % self.request.method)
        self.fill_context()
