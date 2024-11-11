from sentence_transformers import SentenceTransformer
import csv

embedder = SentenceTransformer('all-MiniLM-L6-v2')


# Function to generate embeddings
def generate_embeddings(texts):
    if isinstance(texts, str):
        texts = [texts]  # Ensure input is a list of texts
    embeddings = embedder.encode(texts, convert_to_tensor=False).tolist()  # Encode and return as list
    return embeddings

# Function to add questions to ChromaDB with full metadata
def add_questions_from_csv_to_db(csv_file_path, collection, db_connection):
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for idx, row in enumerate(reader):
            question_text = row['question']
            answer_text = row['answer']
            level = row['level']  # Assuming you have a 'level' column in the CSV
            status = row['status']  # Assuming you have a 'status' column in the CSV
            
            # Generate a unique ID for each question (using index)
            unique_id = str(idx + 1)  # Starting from 1, you can adjust as needed
            
            # Generate embedding for the question
            embedding = generate_embeddings(question_text)[0]
            
            # Store question and answer with full metadata in ChromaDB
            collection.add(
                ids=[unique_id],  # Using the generated unique ID
                metadatas=[{
                    'question_text': question_text,
                    'answer_text': answer_text,
                    'level': level,
                    'status': status
                }],
                embeddings=[embedding]
            )
            # Add the metadata to SQLite database
            cursor = db_connection.cursor()
            cursor.execute("INSERT INTO questions (id, question, answer, level, status) VALUES (?, ?, ?, ?, ?)",
                           (unique_id, question_text, answer_text, level, status))
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
        metadata = results['metadatas'][0][retrieved_ids.index(retrieved_id)]  # Get metadata for the matching ID
        question_text = metadata['question_text']
        answer_text = metadata['answer_text']
        level = metadata['level']
        status = metadata['status']

        # Add the found question and metadata to the list
        relevant_questions.append({
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
def get_questions_by_level_from_sqlite(level, db_connection, n_results):
    cursor = db_connection.cursor()
    
    # Base query to fetch questions by level
    query = "SELECT id, question, answer, level, status FROM questions WHERE level=?"
    
    # If n_results is specified, add LIMIT to the query
    if n_results:
        query += " LIMIT ?"
        cursor.execute(query, (level, n_results))
    else:
        cursor.execute(query, (level,))
    
    rows = cursor.fetchall()

    # If no questions are found
    if not rows:
        return f"No relevant questions found for level '{level}'."

    relevant_questions = []
    for row in rows:
        relevant_questions.append({
            'question': row[1],
            'answer': row[2],
            'level': row[3],
            'status': row[4]
        })

    return relevant_questions

# Example usage
# csv_file_path = 'datasets/ios_interview_questions.csv'  # Replace with your CSV path
# add_questions_from_csv_to_db(csv_file_path)

# Now, you can search for relevant questions by theme
# theme = "Рекурсия"
# n_results = 3
# relevant_questions = get_relevant_question_by_theme(theme, n_results)

# if isinstance(relevant_questions, str):
#     print(relevant_questions)  # No relevant questions found
# else:
#     for idx, question in enumerate(relevant_questions):
#         print(f"Question {idx + 1}: {question['question']}")
#         print(f"Answer: {question['answer']}")
#         print(f"Level: {question['level']}")
#         print(f"Status: {question['status']}")
#         print("------")

# client = chromadb.HttpClient(host='localhost', port=8000)
# collection = client.get_or_create_collection(name="documents_store_3")

# Example usage
# level = "Junior"  # You can set the desired level
# n_results = 3  # The number of results you want to retrieve
# relevant_questions_from_sqlite = get_questions_by_level_from_sqlite(level, db_connection, n_results)
# if not relevant_questions_from_sqlite:
#     print(f"No relevant questions found for level '{level}' from SQLite.")
# else:
#     for idx, question in enumerate(relevant_questions_from_sqlite):
#         print(f"Question {idx + 1}: {question['question']}")
#         print(f"Answer: {question['answer']}")
#         print(f"Level: {question['level']}")
#         print(f"Status: {question['status']}")
#         print("------")