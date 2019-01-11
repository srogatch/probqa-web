# To start with a fresh engine (intentially no easy way in admin):
TRUNCATE `probqa1`.`pqawv1_knowledgebase`;
UPDATE probqa1.pqawv1_question SET pqa_id=NULL WHERE pqa_id IS NOT NULL;
UPDATE probqa1.pqawv1_target SET pqa_id=NULL WHERE pqa_id IS NOT NULL
# Quiz IDs are stored in sessions
TRUNCATE `probqa1`.`django_session`;
