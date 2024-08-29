import streamlit as st
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import bcrypt
from datetime import date, timedelta
from init_db import create_database  # Add this line

load_dotenv()

# Database connection
def create_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database='library_management'
        )
        return connection
    except Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

# Helper functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def authenticate_user(username, password):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user and verify_password(password, user['password']):
                return user
        except Error as e:
            st.error(f"Authentication error: {e}")
        finally:
            conn.close()
    return None

def create_user(username, email, password):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            hashed_password = hash_password(password)
            cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                           (username, email, hashed_password))
            conn.commit()
            st.success("User created successfully!")
        except Error as e:
            st.error(f"Error creating user: {e}")
        finally:
            conn.close()

def get_book_stats():
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as total_books, SUM(quantity) as total_quantity FROM books")
            book_stats = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) as total_users FROM users")
            user_stats = cursor.fetchone()
            return book_stats, user_stats
        except Error as e:
            st.error(f"Error fetching stats: {e}")
        finally:
            conn.close()
    return None, None

def get_books_by_category():
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT c.name as category, COUNT(*) as book_count
                FROM books b
                JOIN categories c ON b.category_id = c.category_id
                GROUP BY c.category_id
            """)
            return cursor.fetchall()
        except Error as e:
            st.error(f"Error fetching books by category: {e}")
        finally:
            conn.close()
    return []

def get_top_rated_books_with_availability():
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT b.book_id, b.title, b.cover_image, b.available_quantity, 
                       COALESCE(AVG(r.rating), 0) as avg_rating
                FROM books b
                LEFT JOIN reviews r ON b.book_id = r.book_id
                GROUP BY b.book_id
                ORDER BY avg_rating DESC, b.title
                LIMIT 5
            """)
            return cursor.fetchall()
        except Error as e:
            st.error(f"Error fetching top rated books: {e}")
        finally:
            conn.close()
    return []

def get_borrowed_books(user_id):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT b.title, l.loan_date, l.return_date, b.book_id
                FROM loans l
                JOIN books b ON l.book_id = b.book_id
                WHERE l.user_id = %s AND l.return_date IS NULL
            """, (user_id,))
            return cursor.fetchall()
        except Error as e:
            st.error(f"Error fetching borrowed books: {e}")
        finally:
            conn.close()
    return []

def get_available_books():
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT b.book_id, b.title, b.author, b.available_quantity
                FROM books b
                WHERE b.available_quantity > 0
            """)
            return cursor.fetchall()
        except Error as e:
            st.error(f"Error fetching available books: {e}")
        finally:
            conn.close()
    return []

def borrow_book(user_id, book_id):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            loan_date = date.today()
            cursor.execute("INSERT INTO loans (user_id, book_id, loan_date) VALUES (%s, %s, %s)",
                           (user_id, book_id, loan_date))
            cursor.execute("UPDATE books SET available_quantity = available_quantity - 1 WHERE book_id = %s", (book_id,))
            conn.commit()
            st.success("Book borrowed successfully!")
        except Error as e:
            st.error(f"Error borrowing book: {e}")
        finally:
            conn.close()

def return_book(user_id, book_id):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Update the loan record
            cursor.execute("""
                UPDATE loans 
                SET return_date = CURDATE() 
                WHERE user_id = %s AND book_id = %s AND return_date IS NULL
            """, (user_id, book_id))
            
            # Increase the available quantity of the book
            cursor.execute("""
                UPDATE books 
                SET available_quantity = available_quantity + 1 
                WHERE book_id = %s
            """, (book_id,))
            
            conn.commit()
        except Error as e:
            st.error(f"Error returning book: {e}")
        finally:
            conn.close()

def add_book(title, author, isbn, publication_year, genre, description, quantity, category_id, cover_image):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO books (title, author, isbn, publication_year, genre, description, quantity, available_quantity, category_id, cover_image)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (title, author, isbn, publication_year, genre, description, quantity, quantity, category_id, cover_image))
            conn.commit()
            st.success("Book added successfully!")
        except Error as e:
            st.error(f"Error adding book: {e}")
        finally:
            conn.close()

def get_categories():
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM categories")
            return cursor.fetchall()
        except Error as e:
            st.error(f"Error fetching categories: {e}")
        finally:
            conn.close()
    return []

def search_books(query):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            search = f"%{query}%"
            cursor.execute("""
                SELECT b.*, c.name as category_name
                FROM books b
                LEFT JOIN categories c ON b.category_id = c.category_id
                WHERE b.title LIKE %s OR b.author LIKE %s OR b.isbn LIKE %s
            """, (search, search, search))
            return cursor.fetchall()
        except Error as e:
            st.error(f"Error searching books: {e}")
        finally:
            conn.close()
    return []

def add_review(user_id, book_id, rating, comment):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            review_date = date.today()
            cursor.execute("""
                INSERT INTO reviews (user_id, book_id, rating, comment, review_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, book_id, rating, comment, review_date))
            conn.commit()
            st.success("Review added successfully!")
        except Error as e:
            st.error(f"Error adding review: {e}")
        finally:
            conn.close()

def remove_book(book_id):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # First, remove any associated loans
            cursor.execute("DELETE FROM loans WHERE book_id = %s", (book_id,))
            # Then, remove any associated reviews
            cursor.execute("DELETE FROM reviews WHERE book_id = %s", (book_id,))
            # Finally, remove the book
            cursor.execute("DELETE FROM books WHERE book_id = %s", (book_id,))
            conn.commit()
            st.success("Book removed successfully!")
        except Error as e:
            st.error(f"Error removing book: {e}")
        finally:
            conn.close()

def get_most_borrowed_books():
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT b.title, COUNT(*) as borrow_count
                FROM loans l
                JOIN books b ON l.book_id = b.book_id
                GROUP BY l.book_id
                ORDER BY borrow_count DESC
                LIMIT 5
            """)
            return cursor.fetchall()
        except Error as e:
            st.error(f"Error fetching most borrowed books: {e}")
        finally:
            conn.close()
    return []

def get_overdue_books():
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT b.title, u.username, l.loan_date
                FROM loans l
                JOIN books b ON l.book_id = b.book_id
                JOIN users u ON l.user_id = u.user_id
                WHERE l.return_date IS NULL AND l.loan_date < DATE_SUB(CURDATE(), INTERVAL 14 DAY)
                ORDER BY l.loan_date
            """)
            return cursor.fetchall()
        except Error as e:
            st.error(f"Error fetching overdue books: {e}")
        finally:
            conn.close()
    return []

def get_book_recommendations(user_id):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT DISTINCT b.book_id, b.title, b.author, b.genre, c.name as category_name
                FROM books b
                JOIN loans l ON b.book_id = l.book_id
                JOIN categories c ON b.category_id = c.category_id
                WHERE l.user_id = %s
                UNION
                SELECT DISTINCT b.book_id, b.title, b.author, b.genre, c.name as category_name
                FROM books b
                JOIN reviews r ON b.book_id = r.book_id
                JOIN categories c ON b.category_id = c.category_id
                WHERE r.user_id = %s AND r.rating >= 4
            """, (user_id, user_id))
            user_preferences = cursor.fetchall()

            if not user_preferences:
                return []

            genres = set(book['genre'] for book in user_preferences)
            categories = set(book['category_name'] for book in user_preferences)

            placeholders = ', '.join(['%s'] * len(genres))
            category_placeholders = ', '.join(['%s'] * len(categories))

            cursor.execute(f"""
                SELECT b.book_id, b.title, b.author, b.genre, c.name as category_name,
                       AVG(r.rating) as avg_rating
                FROM books b
                LEFT JOIN reviews r ON b.book_id = r.book_id
                JOIN categories c ON b.category_id = c.category_id
                WHERE b.genre IN ({placeholders})
                   OR c.name IN ({category_placeholders})
                   AND b.book_id NOT IN (
                       SELECT book_id FROM loans WHERE user_id = %s
                   )
                GROUP BY b.book_id
                ORDER BY avg_rating IS NULL, avg_rating DESC
                LIMIT 5
            """, (*genres, *categories, user_id))

            recommendations = cursor.fetchall()
            return recommendations
        except Error as e:
            st.error(f"Error getting book recommendations: {e}")
        finally:
            conn.close()
    return []

def update_book(book_id, title, author, isbn, publication_year, genre, description, quantity, category_id, cover_image):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE books 
                SET title = %s, author = %s, isbn = %s, publication_year = %s, 
                    genre = %s, description = %s, quantity = %s, 
                    category_id = %s, cover_image = %s
                WHERE book_id = %s
            """, (title, author, isbn, publication_year, genre, description, 
                  quantity, category_id, cover_image, book_id))
            conn.commit()
            st.success("Book updated successfully!")
        except Error as e:
            st.error(f"Error updating book: {e}")
        finally:
            conn.close()

def ensure_database_exists():
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            required_tables = {'users', 'books', 'categories', 'loans', 'reviews'}
            existing_tables = {table[0] for table in tables}
            
            if not required_tables.issubset(existing_tables):
                print("Database tables are missing. Running initialization...")
                create_database()
            else:
                print("Database and tables already exist.")
        except Error as e:
            print(f"Error checking database: {e}")
            create_database()
        finally:
            conn.close()
    else:
        print("Unable to connect to database. Running initialization...")
        create_database()

# Call this function before main
ensure_database_exists()

def main():
    st.title("Library Management System")

    # Sidebar navigation
    st.sidebar.title("Navigation")
    menu_items = ["Home", "Login", "Sign Up", "Borrow", "Book Management", "Review", "Book Search", "Reports"]
    
    if "user" in st.session_state:
        menu_items.append("Logout")
    
    # Replace the buttons with a single selectbox
    selected = st.sidebar.selectbox("Go to", menu_items, key="nav_selectbox")

    if selected == "Home":
        home_page()
    elif selected == "Login":
        login_page()
    elif selected == "Sign Up":
        signup_page()
    elif selected == "Borrow":
        borrow_page()
    elif selected == "Book Management":
        book_management_page()
    elif selected == "Review":
        review_page()
    elif selected == "Book Search":
        book_search_page()
    elif selected == "Reports":
        report_page()
    elif selected == "Logout":
        logout()

def home_page():
    st.header("Welcome to the Library")
    book_stats, user_stats = get_book_stats()
    if book_stats and user_stats:
        st.write(f"Total Books: {book_stats['total_books']}")
        st.write(f"Total Book Quantity: {book_stats['total_quantity']}")
        st.write(f"Total Users: {user_stats['total_users']}")

    st.subheader("Books by Category")
    category_stats = get_books_by_category()
    for cat in category_stats:
        st.write(f"{cat['category']}: {cat['book_count']} books")

    st.subheader("Top Rated Books")
    top_books = get_top_rated_books_with_availability()
    cols = st.columns(5)  # Display up to 5 books in a row
    for i, book in enumerate(top_books):
        with cols[i % 5]:
            st.markdown(f"**{book['title']}**")
            st.write(f"Rating: {book['avg_rating']:.2f}")
            
            if book['cover_image']:
                try:
                    st.image(book['cover_image'], use_column_width=True)
                except Exception as e:
                    st.write("(Image unavailable)")
            else:
                st.write("(No cover image)")
            
            if book['available_quantity'] > 0:
                if st.button("Borrow", key=f"borrow_top_{book['book_id']}"):
                    if "user" in st.session_state:
                        borrow_book(st.session_state.user['user_id'], book['book_id'])
                        st.success(f"You have borrowed '{book['title']}'")
                        st.rerun()
                    else:
                        st.warning("Please login to borrow books")
            else:
                st.write("Not available")

def login_page():
    st.header("Login")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login", key="login_button"):
        user = authenticate_user(username, password)
        if user:
            st.session_state.user = user
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid username or password")

def signup_page():
    st.header("Sign Up")
    new_username = st.text_input("Username", key="signup_username")
    new_email = st.text_input("Email", key="signup_email")
    new_password = st.text_input("Password", type="password", key="signup_password")
    if st.button("Sign Up", key="signup_button"):
        create_user(new_username, new_email, new_password)

def borrow_page():
    if "user" not in st.session_state:
        st.warning("Please login to borrow or return books")
        return

    st.header("Borrow and Return Books")
    
    # Borrowed Books Section
    st.subheader("Your Borrowed Books")
    borrowed_books = get_borrowed_books(st.session_state.user['user_id'])
    if borrowed_books:
        for i, book in enumerate(borrowed_books):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{book['title']} - Borrowed on: {book['loan_date']}")
            with col2:
                if st.button(f"Return", key=f"return_{book['book_id']}_{i}"):
                    return_book(st.session_state.user['user_id'], book['book_id'])
                    st.success(f"You have returned '{book['title']}'")
                    st.rerun()
    else:
        st.info("You haven't borrowed any books yet.")

    # Available Books Section
    st.subheader("Available Books")
    available_books = get_available_books()
    for book in available_books:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"{book['title']} by {book['author']} - Available: {book['available_quantity']}")
        with col2:
            if st.button(f"Borrow '{book['title']}'", key=f"borrow_{book['book_id']}"):
                borrow_book(st.session_state.user['user_id'], book['book_id'])
                st.success(f"You have borrowed '{book['title']}'")
                st.rerun()

    # Book Recommendations Section
    st.subheader("Recommended Books")
    recommendations = get_book_recommendations(st.session_state.user['user_id'])
    if recommendations:
        for book in recommendations:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{book['title']} by {book['author']} - Genre: {book['genre']}, Category: {book['category_name']}")
                if 'avg_rating' in book and book['avg_rating']:
                    st.write(f"Average Rating: {book['avg_rating']:.2f}")
            with col2:
                if st.button(f"Borrow '{book['title']}'", key=f"borrow_rec_{book['book_id']}"):
                    borrow_book(st.session_state.user['user_id'], book['book_id'])
                    st.success(f"You have borrowed '{book['title']}'")
                    st.rerun()
    else:
        st.info("No recommendations available. Try borrowing or reviewing more books!")

def book_management_page():
    if "user" not in st.session_state or not st.session_state.user.get('is_admin', False):
        st.warning("Only admins can access this page")
        return

    st.header("Book Management")

    # Add New Book Section
    st.subheader("Add New Book")
    title = st.text_input("Title", key="add_book_title")
    author = st.text_input("Author", key="add_book_author")
    isbn = st.text_input("ISBN", key="add_book_isbn")
    publication_year = st.number_input("Publication Year", min_value=1000, max_value=date.today().year, key="add_book_year")
    genre = st.text_input("Genre", key="add_book_genre")
    description = st.text_area("Description", key="add_book_description")
    quantity = st.number_input("Quantity", min_value=1, key="add_book_quantity")
    categories = get_categories()
    category_id = st.selectbox("Category", options=[c['category_id'] for c in categories], format_func=lambda x: next(c['name'] for c in categories if c['category_id'] == x), key="add_book_category")
    cover_image = st.text_input("Cover Image URL", key="add_book_cover")

    if st.button("Add Book", key="add_book_button"):
        add_book(title, author, isbn, publication_year, genre, description, quantity, category_id, cover_image)

    # Edit Book Section
    st.subheader("Edit Book")
    books = search_books("")  # Get all books
    book_to_edit = st.selectbox("Select a book to edit", 
                                options=[b['book_id'] for b in books], 
                                format_func=lambda x: next(b['title'] for b in books if b['book_id'] == x),
                                key="edit_book_select")
    
    selected_book = next((b for b in books if b['book_id'] == book_to_edit), None)
    
    if selected_book:
        with st.form(key='edit_book_form'):
            edit_title = st.text_input("Title", value=selected_book['title'], key="edit_book_title")
            edit_author = st.text_input("Author", value=selected_book['author'], key="edit_book_author")
            edit_isbn = st.text_input("ISBN", value=selected_book['isbn'], key="edit_book_isbn")
            edit_publication_year = st.number_input("Publication Year", min_value=1000, max_value=date.today().year, value=selected_book['publication_year'], key="edit_book_year")
            edit_genre = st.text_input("Genre", value=selected_book['genre'], key="edit_book_genre")
            edit_description = st.text_area("Description", value=selected_book['description'], key="edit_book_description")
            edit_quantity = st.number_input("Quantity", min_value=1, value=selected_book['quantity'], key="edit_book_quantity")
            categories = get_categories()
            category_ids = [c['category_id'] for c in categories]
            default_index = category_ids.index(selected_book['category_id']) if selected_book['category_id'] in category_ids else 0
            edit_category_id = st.selectbox("Category", 
                                            options=category_ids,
                                            index=default_index,
                                            format_func=lambda x: next((c['name'] for c in categories if c['category_id'] == x), "Unknown"),
                                            key="edit_book_category")
            edit_cover_image = st.text_input("Cover Image URL", value=selected_book['cover_image'], key="edit_book_cover")

            if st.form_submit_button("Update Book"):
                update_book(book_to_edit, edit_title, edit_author, edit_isbn, edit_publication_year, 
                            edit_genre, edit_description, edit_quantity, edit_category_id, edit_cover_image)
                st.rerun()

    # Remove Book Section
    st.subheader("Remove Book")
    books = search_books("")  # Get all books
    book_to_remove = st.selectbox("Select a book to remove", 
                                  options=[b['book_id'] for b in books], 
                                  format_func=lambda x: next(b['title'] for b in books if b['book_id'] == x),
                                  key="remove_book_select")
    
    if st.button("Remove Book", key="remove_book_button"):
        remove_book(book_to_remove)
        st.success("Book removed successfully!")
        st.rerun()

def review_page():
    if "user" not in st.session_state:
        st.warning("Please login to review books")
        return

    st.header("Review Books")
    books = search_books("")  # Get all books
    book_id = st.selectbox("Select a book to review", options=[b['book_id'] for b in books], format_func=lambda x: next(b['title'] for b in books if b['book_id'] == x), key="review_book_select")
    rating = st.slider("Rating", 1, 5, 3, key="review_rating")
    comment = st.text_area("Comment", key="review_comment")
    if st.button("Submit Review", key="submit_review_button"):
        add_review(st.session_state.user['user_id'], book_id, rating, comment)

def book_search_page():
    st.header("Book Search")
    search_query = st.text_input("Search for books (title, author, or ISBN)", key="book_search_query")
    if search_query:
        results = search_books(search_query)
        for book in results:
            st.write(f"Title: {book['title']}")
            st.write(f"Author: {book['author']}")
            st.write(f"ISBN: {book['isbn']}")
            st.write(f"Category: {book['category_name']}")
            st.write("---")

def report_page():
    if "user" not in st.session_state or not st.session_state.user.get('is_admin', False):
        st.warning("Only admins can access this page")
        return

    st.header("Library Reports")

    # General Statistics
    st.subheader("General Statistics")
    book_stats, user_stats = get_book_stats()
    if book_stats and user_stats:
        st.write(f"Total Books: {book_stats['total_books']}")
        st.write(f"Total Book Quantity: {book_stats['total_quantity']}")
        st.write(f"Total Users: {user_stats['total_users']}")

    # Books by Category
    st.subheader("Books by Category")
    category_stats = get_books_by_category()
    category_data = {cat['category']: cat['book_count'] for cat in category_stats}
    st.bar_chart(category_data)

    # Top Rated Books
    st.subheader("Top Rated Books")
    top_books = get_top_rated_books_with_availability()
    for book in top_books:
        st.write(f"{book['title']} - Average Rating: {book['avg_rating']:.2f}")

    # Most Borrowed Books
    st.subheader("Most Borrowed Books")
    most_borrowed = get_most_borrowed_books()
    for book in most_borrowed:
        st.write(f"{book['title']} - Borrowed {book['borrow_count']} times")

    # Overdue Books
    st.subheader("Overdue Books")
    overdue_books = get_overdue_books()
    for book in overdue_books:
        st.write(f"{book['title']} - Borrowed by {book['username']} on {book['loan_date']}")

def logout():
    if "user" in st.session_state:
        del st.session_state.user
    st.success("Logged out successfully!")
    st.rerun()

if __name__ == "__main__":
    main()