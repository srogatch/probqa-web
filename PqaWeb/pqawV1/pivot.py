import ProbQAInterop.ProbQA as probqa


class Pivot:
    instance = None

    def __init__(self):
        self.engine = None

    def set_engine(self, engine: probqa.PqaEngine):
        self.engine = engine

    def get_engine(self) -> probqa.PqaEngine:
        return self.engine


Pivot.instance = Pivot()
