import pickle
import sqlite3
import streamlit as st
import numpy as np

# Set up the header and intro text for user guidance
st.title("📚 Book Recommender System")
st.write("Discover books you'll love based on your preferences! Select a book to get recommendations, and provide feedback to personalize suggestions.")

# Load model and data artifacts
model = pickle.load(open('artifacts/model.pkl', 'rb'))
book_names = pickle.load(open('artifacts/book_names.pkl', 'rb'))
final_rating = pickle.load(open('artifacts/final_rating.pkl', 'rb'))
book_pivot = pickle.load(open('artifacts/book_pivot.pkl', 'rb'))

# Connect to SQLite database to store user feedback
conn = sqlite3.connect('feedback.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        user_id INTEGER,
        book_name TEXT,
        feedback TEXT
    )
''')
conn.commit()

def save_feedback(user_id, book_name, feedback):
    cursor.execute("INSERT INTO feedback (user_id, book_name, feedback) VALUES (?, ?, ?)", (user_id, book_name, feedback))
    conn.commit()

# Function to get poster URLs for recommended books
def fetch_poster(suggestion):
    book_name = []
    ids_index = []
    poster_url = []

    for book_id in suggestion:
        book_name.append(book_pivot.index[book_id])

    for name in book_name[0]: 
        ids = np.where(final_rating['title'] == name)[0][0]
        ids_index.append(ids)

    for idx in ids_index:
        url = final_rating.iloc[idx]['image_url']
        poster_url.append(url)

    return poster_url

# Function to generate book recommendations with an explanation
def recommend_book(book_name):
    books_list = []
    book_id = np.where(book_pivot.index == book_name)[0][0]
    distance, suggestion = model.kneighbors(book_pivot.iloc[book_id, :].values.reshape(1, -1), n_neighbors=8)
    poster_url = fetch_poster(suggestion)
    
    for i in range(len(suggestion)):
        books = book_pivot.index[suggestion[i]]
        for j in books:
            books_list.append(j)
    
    # Generate explanations for recommendations
    explanations = [f"People who read '{book_name}' also enjoyed '{book}'" for book in books_list[1:5]]
    return books_list, poster_url, explanations

# Book selection dropdown
selected_books = st.selectbox("Type or select a book from the dropdown", book_names)

# User ID placeholder (in practice, you might get this from user login info)
user_id = 1  # Static user ID for demonstration

# Show recommendations with explanations when button is clicked
if st.button('Show Recommendations'):
    recommended_books, poster_url, explanations = recommend_book(selected_books)
    
    # Display recommendations with explanations and feedback options
    for i, (book, explanation) in enumerate(zip(recommended_books[1:5], explanations), start=1):  # Skip first to avoid repeating search
        col1, col2, col3 = st.columns([1, 1, 2])
        
        # Display the book title and image
        with col1:
            st.text(book)
        with col2:
            st.image(poster_url[i])
        
        # Explanation and feedback buttons
        with col3:
            st.write(explanation)  # Show explanation next to the book
            if st.button(f'❤️ Like {book}', key=f'like_{i}'):
                save_feedback(user_id, book, 'like')
                st.success(f'You liked {book}')
            if st.button(f'💔 Dislike {book}', key=f'dislike_{i}'):
                save_feedback(user_id, book, 'dislike')
                st.warning(f'You disliked {book}')

# Confirm that feedback is stored and will be used to improve recommendations
st.write("Your feedback helps us improve our recommendations!")
