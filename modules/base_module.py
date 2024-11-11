class TrackModule:
    def __init__(self):
        pass

    def fetch_questions(self):
        # Method to be implemented by child classes
        raise NotImplementedError("This method should be overridden in a subclass")

    def generate_report(self, answers):
        # Method to be implemented by child classes
        raise NotImplementedError("This method should be overridden in a subclass")