from modules.base_module import TrackModule
from utils import generate_content

class MLTrackModule(TrackModule):
    def __init__(self, user_preferences, rag_manager):
        self.user_preferences = user_preferences
        self.rag_manager = rag_manager

    def get_questions_by_theme(self):
        # Retrieve questions related to the given theme using embeddings or any other logic
        return self.rag_manager.get_questions_by_theme(self.user_preferences['theme'], self.user_preferences['number_of_questions'])

    def get_questions_by_level(self):
        # Fetch questions for a particular level
        print(self.user_preferences['level'], self.rag_manager.sglite, self.user_preferences['number_of_questions'])
        return self.rag_manager.get_questions_by_level(self.user_preferences['level'], self.user_preferences['number_of_questions'])

    def fetch_questions(self):
        # Fetch ML-specific questions based on level and theme
        if self.user_preferences['theme']:
            questions = self.get_questions_by_theme()
        else:
            questions = self.get_questions_by_level()
        return questions

    def generate_report(self, answers):
        # Compare answers, calculate score, and generate report
        prompt = f"""Write report based on user's answers: {answers}. 
        The questions and proper answers are: {questions}.
        Report must be in the following format:

        1. Question: 
        Score + 
        2. Question: 
        Score - 
        User's mistake 
        Proper Answer
        ...

        Total score: number of '+' divided by number of questions.
        Recommendations to repeat: (list of themes in which user made a mistake)
        """
        content = generate_content(prompt)
        return content