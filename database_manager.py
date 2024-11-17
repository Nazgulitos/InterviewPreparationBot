import sqlite3
import chromadb
from sentence_transformers import SentenceTransformer
import csv
import fitz 
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

embedder = SentenceTransformer('all-MiniLM-L6-v2')
IDX = 0

# Function to generate embeddings
def generate_embeddings(texts):
    if isinstance(texts, str):
        texts = [texts]
    embeddings = embedder.encode(texts, convert_to_tensor=False).tolist()
    return embeddings

# Function to add questions to ChromaDB with full metadata
def add_questions_from_csv_to_db(csv_file_path, db_connection, theme):
    global IDX
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for idx, row in enumerate(reader):
            question_text = row['question']
            answer_text = row['answer']
            level = row['level']
            status = row['status']
            unique_id = str(IDX) 
            # embedding = generate_embeddings(question_text)[0]
            IDX += 1
            
            # Store question and answer with full metadata in ChromaDB
            # collection.add(
            #     ids=[unique_id],
            #     metadatas=[{
            #         'theme': theme,
            #         'question_text': question_text,
            #         'answer_text': answer_text,
            #         'level': level,
            #         'status': status
            #     }],
            #     embeddings=[embedding]
            # )
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

# Function to extract text from a PDF and chunk it into semantically meaningful pieces
def extract_text_from_pdf(pdf_file_path):
    doc = fitz.open(pdf_file_path)
    all_text = []
    
    # Iterate over the pages in the PDF and extract text
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        all_text.append(text)
    
    return "\n".join(all_text)

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

def semantic_chunking(text, min_samples=2, eps=0.5, max_sentences_per_chunk=3):
    # Split the text into sentences
    sentences = text.split('. ')  # Simple sentence splitting, you can use a more advanced tokenizer like spaCy
    
    # Generate embeddings for each sentence
    sentence_embeddings = generate_embeddings(sentences)
    
    # Compute pairwise cosine similarities
    similarity_matrix = cosine_similarity(sentence_embeddings)
    
    # Convert cosine similarity to distance matrix (1 - similarity)
    distance_matrix = 1 - similarity_matrix
    
    # Ensure no negative values in the distance matrix (clip them to 0)
    distance_matrix = np.maximum(distance_matrix, 0)
    
    # Apply DBSCAN clustering to identify semantically similar sentences
    clustering_model = DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed")
    clusters = clustering_model.fit_predict(distance_matrix)
    
    # Group sentences into chunks based on clustering results
    chunks = []
    for cluster_id in np.unique(clusters):
        if cluster_id == -1:  # -1 is the label for noise in DBSCAN
            continue
        chunk_sentences = [sentences[i] for i in range(len(sentences)) if clusters[i] == cluster_id]
        
        # Ensure the chunk does not exceed the max number of sentences
        while len(chunk_sentences) > max_sentences_per_chunk:
            # Split the chunk into smaller parts if it's too large
            chunk = " ".join(chunk_sentences[:max_sentences_per_chunk])
            chunks.append(chunk)
            chunk_sentences = chunk_sentences[max_sentences_per_chunk:]
        
        # Add the remaining sentences as one chunk
        if chunk_sentences:
            chunks.append(" ".join(chunk_sentences))
    
    return chunks

# Function to add PDF content to ChromaDB
def add_pdf_to_chromadb(pdf_file_path, collection, theme):
    global IDX
    text = extract_text_from_pdf(pdf_file_path)
    chunks = semantic_chunking(text)
    
    for chunk in chunks:
        unique_id = str(IDX)
        embedding = generate_embeddings(chunk)[0]
        IDX += 1
        
        # Store the text chunk with metadata in ChromaDB
        collection.add(
            ids=[unique_id],
            metadatas=[{
                'theme': theme,
                'text_chunk': chunk
            }],
            embeddings=[embedding]
        )
        
        print(f"Added chunk to ChromaDB with ID '{unique_id}'.")

# Function to retrieve relevant context from ChromaDB based on a query
def retrieve_context_from_chromadb(query, collection, n_results=3):
    query_embedding = generate_embeddings(query)[0]
    
    # Search for the closest matching embeddings in ChromaDB
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
    
    # Print debug info for the results
    print(f"ChromaDB query results: {results}")  # Debug print
    
    # Retrieve the list of IDs from the query results
    retrieved_ids = results['ids'][0]
    
    # Create a list to store the relevant text chunks
    relevant_context = []
    
    for idx in range(len(retrieved_ids)):
        metadata = results['metadatas'][0][idx]
        text_chunk = metadata['text_chunk']
        
        # Add the relevant chunk and metadata to the list
        relevant_context.append({
            'id': retrieved_ids[idx],
            'theme': metadata['theme'],
            'text_chunk': text_chunk
        })
    
    # If no relevant context found, return a default message
    if not relevant_context:
        return "No relevant context found."
    
    return relevant_context

# # Example usage
# # Assuming you have a ChromaDB collection and a SQLite database connection set up
# collection = chromadb.Client().get_or_create_collection('pdf_collection4')

# # Add PDF to ChromaDB
# add_pdf_to_chromadb('datasets/PDF_ML.pdf', collection, theme='ML_EN')

# # Retrieve context based on a query
# retrieved_context = retrieve_context_from_chromadb('Clustering', collection)
# print(retrieved_context)

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