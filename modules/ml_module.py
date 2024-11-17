from modules.base_module import TrackModule
from modules.question_retriever import QuestionRetriever
from modules.report_generator import ReportGenerator

class MLTrackModule(TrackModule):
    def __init__(self, user_preferences, rag_manager, type_name="ML_EN"):
        self.user_preferences = user_preferences
        self.rag_manager = rag_manager
        self.type_name = type_name
        self.question_retriever = QuestionRetriever(rag_manager)
        self.report_generator = ReportGenerator(rag_manager)

    async def fetch_questions(self):
        if self.user_preferences['theme']:
            questions = await self.question_retriever.get_questions_by_theme(
                self.user_preferences['theme'],
                self.user_preferences['number_of_questions']
            )
        else:
            questions = await self.question_retriever.get_questions_by_level(
                self.type_name,
                self.user_preferences['level'],
                self.user_preferences['number_of_questions']
            )
        return questions

    async def generate_report(self, answers, questions):
        return await self.report_generator.generate_report(answers, questions)