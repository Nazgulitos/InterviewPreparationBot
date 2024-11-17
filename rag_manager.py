from database_manager import add_questions_from_csv_to_db, get_relevant_question_by_theme, get_questions_by_level_from_sqlite, change_status

class RAGManager:
    def __init__(self, chromadb_connection, sglite_connection):
        self.chromadb = chromadb_connection  # This can be your SQL database or any other data source
        self.sglite = sglite_connection  # This can be your SQL database or any other data source

    def get_questions_by_theme(self, theme, n_results):
        # Retrieve questions related to the given theme using embeddings or any other logic
        return get_relevant_question_by_theme(theme, self.chromadb, n_results)

    def get_questions_by_level(self, theme, level, n_results):
        # Fetch questions for a particular level
        return get_questions_by_level_from_sqlite(theme, level, self.sglite, n_results)
    
    def generate_report(self):
        # Compare answers, calculate score, and generate report
        pass
    def change_status(self, id, status):
        return change_status(id, status, self.sglite)