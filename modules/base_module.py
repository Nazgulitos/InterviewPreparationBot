class TrackModule:
    def __init__(self):
        pass

    def fetch_questions(self):
        raise NotImplementedError("This method should be overridden in a subclass")

    def generate_report(self, answers):
        raise NotImplementedError("This method should be overridden in a subclass")