import sqlite3
import chromadb
from sentence_transformers import SentenceTransformer
import csv

embedder = SentenceTransformer('all-MiniLM-L6-v2')
IDX = 0

# Function to generate embeddings
def generate_embeddings(texts):
    if isinstance(texts, str):
        texts = [texts]
    embeddings = embedder.encode(texts, convert_to_tensor=False).tolist()
    return embeddings

# Function to add questions to ChromaDB with full metadata
def add_questions_from_csv_to_db(csv_file_path, collection, db_connection, theme):
    global IDX
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for idx, row in enumerate(reader):
            question_text = row['question']
            answer_text = row['answer']
            level = row['level']
            status = row['status']
            unique_id = str(IDX) 
            embedding = generate_embeddings(question_text)[0]
            IDX += 1
            
            # Store question and answer with full metadata in ChromaDB
            collection.add(
                ids=[unique_id],
                metadatas=[{
                    'theme': theme,
                    'question_text': question_text,
                    'answer_text': answer_text,
                    'level': level,
                    'status': status
                }],
                embeddings=[embedding]
            )
            # Add the metadata to SQLite database
            cursor = db_connection.cursor()
            cursor.execute("INSERT INTO questions (id, theme, question, answer, level, status) VALUES (?, ?, ?, ?, ?, ?)",
                           (unique_id, theme, question_text, answer_text, level, status))
            db_connection.commit()

            print(f"Added question '{question_text}' with level '{level}' and status '{status}' to ChromaDB.")

# Function to find relevant questions by theme
def get_relevant_question_by_theme(theme, collection, n_results):
    # Generate embedding for the theme provided by the user
    theme_embedding = generate_embeddings(theme)[0]

    # Search for the closest matching question embeddings in ChromaDB
    results = collection.query(query_embeddings=[theme_embedding], n_results=n_results)  # Get n most relevant documents

    # Print debug info for the results
    print(f"ChromaDB query results: {results}")  # Debug print

    # Retrieve the list of IDs from the query results
    retrieved_ids = [int(id_str) for id_str in results['ids'][0]]  # Assuming ids are in a list inside another list
    print(f"Retrieved IDs: {retrieved_ids}")  # Debug print

    # Create a list to store the relevant questions and metadata
    relevant_questions = []

    # Retrieve the corresponding question, answer, level, and status from ChromaDB using the retrieved IDs
    for retrieved_id in retrieved_ids:
        theme_name = results['metadatas'][0][retrieved_ids.index(retrieved_id)]['theme']
        metadata = results['metadatas'][0][retrieved_ids.index(retrieved_id)]  # Get metadata for the matching ID
        question_text = metadata['question_text']
        answer_text = metadata['answer_text']
        level = metadata['level']
        status = metadata['status']

        # Add the found question and metadata to the list
        relevant_questions.append({
            'id': retrieved_id,
            'theme': theme_name,
            'question': question_text,
            'answer': answer_text,
            'level': level,
            'status': status
        })

    # If no relevant questions found, return a default message
    if not relevant_questions:
        return "No relevant questions found for this theme."

    return relevant_questions

# Function to query SQLite for questions by level
def get_questions_by_level_from_sqlite(theme, level, db_connection, n_results):
    cursor = db_connection.cursor()
    
    # Base query to fetch questions by level
    query = "SELECT id, theme, question, answer, level, status FROM questions WHERE theme=? AND level=? and status='none'"
    
    # If n_results is specified, add LIMIT to the query
    if n_results:
        query += " LIMIT ?"
        cursor.execute(query, (theme, level, n_results))
    else:
        cursor.execute(query, (theme, level,))
    
    rows = cursor.fetchall()

    # If no questions are found
    if not rows:
        return f"No relevant questions found for theme '{theme}' and level '{level}'."

    relevant_questions = []
    for row in rows:
        relevant_questions.append({
            'id': row[0],
            'theme': row[1],
            'question': row[2],
            'answer': row[3],
            'level': row[4],
            'status': row[5]
        })

    return relevant_questions
def change_status(id, status, db_connection):
    cursor = db_connection.cursor()

    # Debug print: Display the ID and status being updated
    print(f"Attempting to update status for ID: {id} to '{status}'")

    cursor.execute("UPDATE questions SET status=? WHERE id=?", (status, id))
    db_connection.commit()

    # Debug print: Check the number of rows affected
    if cursor.rowcount > 0:
        print(f"Status updated successfully for ID: {id}")
    else:
        print(f"No rows were updated. Check if ID: {id} exists in the database.")

    return True
# Change the status of question with ID 3 to 'reviewed'
# Example usage
# client = chromadb.HttpClient(host='localhost', port=8000)
# collection = client.get_or_create_collection(name="chromadb_demo")
# def create_sqlite_db(path):
#     connection = sqlite3.connect(path)
#     cursor = connection.cursor()
#     cursor.execute('''CREATE TABLE IF NOT EXISTS questions (
#                         id TEXT PRIMARY KEY,
#                         theme TEXT,
#                         question TEXT,
#                         answer TEXT,
#                         level TEXT,
#                         status TEXT)''')
#     connection.commit()
#     return connection

# db_path = 'sglite_demo.db'
# sqlite_connection = create_sqlite_db(db_path)

# ## IOS_RU
# theme_name = "IOS_RU"
# csv_file_path = 'datasets/ios_interview_questions_ru.csv'
# add_questions_from_csv_to_db(csv_file_path, collection, sqlite_connection, theme_name)

# ## ML_EN
# theme_name = "ML_EN"
# csv_file_path = 'datasets/ml_interview_questions_en.csv'
# add_questions_from_csv_to_db(csv_file_path, collection, sqlite_connection, theme_name)

# print(IDX) #903