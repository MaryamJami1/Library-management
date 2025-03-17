import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json
import time

# API URL - Change this to your Flask backend URL
API_URL = "http://localhost:5000"

# Page configuration
st.set_page_config(
    page_title="Library Management System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "login"
if 'books' not in st.session_state:
    st.session_state.books = []
if 'page_num' not in st.session_state:
    st.session_state.page_num = 1
if 'total_pages' not in st.session_state:
    st.session_state.total_pages = 1
if 'book_to_edit' not in st.session_state:
    st.session_state.book_to_edit = None
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'book_to_delete' not in st.session_state:
    st.session_state.book_to_delete = None
# Notification system
if 'notification' not in st.session_state:
    st.session_state.notification = None
if 'notification_type' not in st.session_state:
    st.session_state.notification_type = None
if 'notification_time' not in st.session_state:
    st.session_state.notification_time = None

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .book-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #1E3A8A;
    }
    .book-author {
        font-style: italic;
        color: #4B5563;
    }
    .book-year {
        color: #6B7280;
    }
    .book-genre {
        background-color: #E5E7EB;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
    }
    .read-status {
        font-weight: bold;
    }
    .read-yes {
        color: #10B981;
    }
    .read-no {
        color: #EF4444;
    }
    .btn-primary {
        background-color: #1E3A8A;
        color: white;
    }
    .btn-danger {
        background-color: #EF4444;
        color: white;
    }
    .btn-success {
        background-color: #10B981;
        color: white;
    }
    .pagination {
        display: flex;
        justify-content: center;
        margin-top: 20px;
    }
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        padding: 15px 25px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        animation: fadeIn 0.3s, fadeOut 0.3s 3.7s;
        width: 300px;
    }
    .notification-success {
        background-color: #10B981;
        color: white;
    }
    .notification-error {
        background-color: #EF4444;
        color: white;
    }
    .notification-info {
        background-color: #3B82F6;
        color: white;
    }
    @keyframes fadeIn {
        from {opacity: 0;}
        to {opacity: 1;}
    }
    @keyframes fadeOut {
        from {opacity: 1;}
        to {opacity: 0;}
    }
</style>
""", unsafe_allow_html=True)

# Notification system
def show_notification(message, type="success"):
    st.session_state.notification = message
    st.session_state.notification_type = type
    st.session_state.notification_time = datetime.now()

def display_notification():
    if st.session_state.notification:
        # Check if notification should expire (after 4 seconds)
        if st.session_state.notification_time:
            time_diff = (datetime.now() - st.session_state.notification_time).total_seconds()
            if time_diff > 4:
                st.session_state.notification = None
                st.session_state.notification_type = None
                st.session_state.notification_time = None
                return
        
        # Display notification based on type
        notification_class = f"notification notification-{st.session_state.notification_type}"
        notification_html = f"""
        <div class="{notification_class}">
            {st.session_state.notification}
        </div>
        """
        st.markdown(notification_html, unsafe_allow_html=True)

# Helper functions for API calls
def make_api_request(endpoint, method="GET", data=None, token=None, params=None):
    url = f"{API_URL}/{endpoint}"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    if method == "GET":
        response = requests.get(url, headers=headers, params=params)
    elif method == "POST":
        headers["Content-Type"] = "application/json"
        response = requests.post(url, headers=headers, data=json.dumps(data))
    elif method == "PUT":
        headers["Content-Type"] = "application/json"
        response = requests.put(url, headers=headers, data=json.dumps(data))
    elif method == "DELETE":
        response = requests.delete(url, headers=headers)
    
    return response

def login_user(email, password):
    try:
        response = make_api_request("login", method="POST", data={"email": email, "password": password})
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["token"]
            st.session_state.user_email = email
            st.session_state.current_page = "dashboard"
            show_notification(f"Welcome back, {email}!", "success")
            return True, "Login successful!"
        else:
            error_msg = response.json().get("message", "Login failed. Please check your credentials.")
            return False, error_msg
    except Exception as e:
        return False, f"Error connecting to server: {str(e)}"

def register_user(email, password):
    try:
        response = make_api_request("register", method="POST", data={"email": email, "password": password})
        
        if response.status_code == 201:
            show_notification("Registration successful! Please login.", "success")
            return True, "Registration successful! Please login."
        else:
            error_msg = response.json().get("message", "Registration failed.")
            return False, error_msg
    except Exception as e:
        return False, f"Error connecting to server: {str(e)}"

def logout_user():
    try:
        if st.session_state.token:
            make_api_request("logout", method="POST", token=st.session_state.token)
        
        # Clear session state
        user_email = st.session_state.user_email
        st.session_state.token = None
        st.session_state.user_email = None
        st.session_state.current_page = "login"
        st.session_state.books = []
        show_notification(f"Goodbye, {user_email}! You've been logged out.", "info")
        return True, "Logout successful!"
    except Exception as e:
        return False, f"Error during logout: {str(e)}"

def get_books(page=1, per_page=10):
    try:
        params = {"page": page, "per_page": per_page}
        response = make_api_request("books", token=st.session_state.token, params=params)
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.books = data.get("books", [])
            st.session_state.page_num = data.get("page", 1)
            st.session_state.total_pages = data.get("pages", 1)
            return True, "Books retrieved successfully!"
        else:
            error_msg = response.json().get("message", "Failed to retrieve books.")
            return False, error_msg
    except Exception as e:
        return False, f"Error connecting to server: {str(e)}"

def add_book(title, author, year, genre, read):
    try:
        data = {
            "title": title,
            "author": author,
            "year": year,
            "genre": genre,
            "read": read
        }
        
        response = make_api_request("add_book", method="POST", data=data, token=st.session_state.token)
        
        if response.status_code == 201:
            show_notification(f"Book '{title}' has been added to your library!", "success")
            return True, "Book added successfully!"
        else:
            error_msg = response.json().get("message", "Failed to add book.")
            return False, error_msg
    except Exception as e:
        return False, f"Error connecting to server: {str(e)}"

def update_book(book_id, title, author, year, genre, read):
    try:
        data = {
            "title": title,
            "author": author,
            "year": year,
            "genre": genre,
            "read": read
        }
        
        response = make_api_request(f"update_book/{book_id}", method="PUT", data=data, token=st.session_state.token)
        
        if response.status_code == 200:
            show_notification(f"Book '{title}' has been updated successfully!", "success")
            return True, "Book updated successfully!"
        else:
            error_msg = response.json().get("message", "Failed to update book.")
            return False, error_msg
    except Exception as e:
        return False, f"Error connecting to server: {str(e)}"

def delete_book(book_id):
    try:
        response = make_api_request(f"delete_book/{book_id}", method="DELETE", token=st.session_state.token)
        
        if response.status_code == 200:
            show_notification(f"Book has been removed from your library.", "info")
            return True, "Book deleted successfully!"
        else:
            error_msg = response.json().get("message", "Failed to delete book.")
            return False, error_msg
    except Exception as e:
        return False, f"Error connecting to server: {str(e)}"

def get_book_by_id(book_id):
    try:
        response = make_api_request(f"book/{book_id}", token=st.session_state.token)
        
        if response.status_code == 200:
            return True, response.json()
        else:
            error_msg = response.json().get("message", "Failed to retrieve book.")
            return False, error_msg
    except Exception as e:
        return False, f"Error connecting to server: {str(e)}"

# Navigation functions
def navigate_to(page):
    st.session_state.current_page = page

# UI Components
def render_login_page():
    st.markdown("<h1 class='main-header'>📚 Library Management System</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        
        # Tabs for login and register
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.subheader("Login to Your Account")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", use_container_width=True):
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    success, message = login_user(email, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        
        with tab2:
            st.subheader("Create New Account")
            email = st.text_input("Email", key="register_email")
            password = st.text_input("Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            
            if st.button("Register", use_container_width=True):
                if not email or not password or not confirm_password:
                    st.error("Please fill in all fields.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters long.")
                else:
                    success, message = register_user(email, password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
        
        st.markdown("</div>", unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.markdown("<h2 class='sub-header'>📚 Library Management</h2>", unsafe_allow_html=True)
        st.markdown(f"Logged in as: **{st.session_state.user_email}**")
        st.divider()
        
        st.button("📊 Dashboard", on_click=navigate_to, args=("dashboard",), use_container_width=True)
        st.button("📚 My Books", on_click=navigate_to, args=("books",), use_container_width=True)
        st.button("➕ Add New Book", on_click=navigate_to, args=("add_book",), use_container_width=True)
        
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            success, message = logout_user()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

def render_dashboard():
    st.markdown("<h1 class='main-header'>Dashboard</h1>", unsafe_allow_html=True)
    
    # Refresh books data
    get_books()
    
    # Stats cards
    col1, col2, col3 = st.columns(3)
    
    total_books = len(st.session_state.books)
    read_books = sum(1 for book in st.session_state.books if book.get("read", False))
    unread_books = total_books - read_books
    
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.metric("Total Books", total_books)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.metric("Books Read", read_books)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.metric("Books to Read", unread_books)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Recent books
    st.markdown("<h2 class='sub-header'>Recently Added Books</h2>", unsafe_allow_html=True)
    
    if st.session_state.books:
        # Sort books by created_at if available, otherwise just take the first few
        recent_books = sorted(
            st.session_state.books, 
            key=lambda x: x.get("created_at", ""), 
            reverse=True
        )[:5]
        
        for book in recent_books:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"<div class='book-title'>{book.get('title')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='book-author'>by {book.get('author')}</div>", unsafe_allow_html=True)
                st.markdown(f"<span class='book-genre'>{book.get('genre')}</span> <span class='book-year'>({book.get('year')})</span>", unsafe_allow_html=True)
            
            with col2:
                read_status = "Yes" if book.get("read", False) else "No"
                read_class = "read-yes" if book.get("read", False) else "read-no"
                st.markdown(f"<div class='read-status'>Read: <span class='{read_class}'>{read_status}</span></div>", unsafe_allow_html=True)
            
            st.divider()
    else:
        st.info("No books found. Add some books to your library!")

def render_delete_confirmation():
    if st.session_state.book_to_delete:
        book = st.session_state.book_to_delete
        book_id = book.get("_id")
        book_title = book.get("title")
        
        st.warning(f"Are you sure you want to delete '{book_title}'?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Delete"):
                success, message = delete_book(book_id)
                if success:
                    show_notification(f"Book '{book_title}' has been deleted.", "info")
                    st.session_state.book_to_delete = None
                    # Refresh books after deletion
                    get_books(page=st.session_state.page_num)
                    st.rerun()
                else:
                    st.error(message)
        with col2:
            if st.button("Cancel"):
                st.session_state.book_to_delete = None
                st.rerun()

def render_books_page():
    st.markdown("<h1 class='main-header'>My Books</h1>", unsafe_allow_html=True)
    
    # Show delete confirmation if needed
    if st.session_state.book_to_delete:
        render_delete_confirmation()
        return
    
    # Search and filter
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input("Search books by title or author", value=st.session_state.search_query)
        st.session_state.search_query = search_query
    
    with col2:
        filter_option = st.selectbox("Filter by", ["All Books", "Read", "Unread"])
    
    # Refresh books data
    success, message = get_books(page=st.session_state.page_num)
    
    if not success:
        st.error(message)
        return
    
    # Filter books based on search query and filter option
    filtered_books = st.session_state.books
    
    if search_query:
        filtered_books = [
            book for book in filtered_books 
            if search_query.lower() in book.get("title", "").lower() or 
               search_query.lower() in book.get("author", "").lower()
        ]
    
    if filter_option == "Read":
        filtered_books = [book for book in filtered_books if book.get("read", False)]
    elif filter_option == "Unread":
        filtered_books = [book for book in filtered_books if not book.get("read", False)]
    
    # Display books
    if filtered_books:
        for book in filtered_books:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"<div class='book-title'>{book.get('title')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='book-author'>by {book.get('author')}</div>", unsafe_allow_html=True)
                st.markdown(f"<span class='book-genre'>{book.get('genre')}</span> <span class='book-year'>({book.get('year')})</span>", unsafe_allow_html=True)
            
            with col2:
                read_status = "Yes" if book.get("read", False) else "No"
                read_class = "read-yes" if book.get("read", False) else "read-no"
                st.markdown(f"<div class='read-status'>Read: <span class='{read_class}'>{read_status}</span></div>", unsafe_allow_html=True)
                
                # Toggle read status button
                if st.button("Toggle Read Status", key=f"toggle_{book.get('_id')}"):
                    updated_book = book.copy()
                    updated_book["read"] = not book.get("read", False)
                    success, message = update_book(
                        book.get("_id"), 
                        book.get("title"), 
                        book.get("author"), 
                        book.get("year"), 
                        book.get("genre"), 
                        not book.get("read", False)
                    )
                    if success:
                        show_notification(
                            f"Book '{book.get('title')}' marked as {'read' if not book.get('read', False) else 'unread'}.", 
                            "success"
                        )
                        st.rerun()
            
            with col3:
                book_id = book.get("_id")
                
                if st.button("Edit", key=f"edit_{book_id}"):
                    st.session_state.book_to_edit = book
                    navigate_to("edit_book")
                
                # Delete button with confirmation
                if st.button("Delete", key=f"delete_{book_id}"):
                    st.session_state.book_to_delete = book
                    st.rerun()
            
            st.divider()
        
        # Pagination controls
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<div class='pagination'>", unsafe_allow_html=True)
            
            prev_disabled = st.session_state.page_num <= 1
            next_disabled = st.session_state.page_num >= st.session_state.total_pages
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                if st.button("⏮️ First", disabled=prev_disabled):
                    st.session_state.page_num = 1
                    get_books(page=st.session_state.page_num)
                    st.rerun()
            
            with col2:
                if st.button("◀️ Previous", disabled=prev_disabled):
                    st.session_state.page_num -= 1
                    get_books(page=st.session_state.page_num)
                    st.rerun()
            
            with col3:
                st.markdown(f"Page {st.session_state.page_num} of {st.session_state.total_pages}")
            
            with col4:
                if st.button("Next ▶️", disabled=next_disabled):
                    st.session_state.page_num += 1
                    get_books(page=st.session_state.page_num)
                    st.rerun()
            
            with col5:
                if st.button("Last ⏭️", disabled=next_disabled):
                    st.session_state.page_num = st.session_state.total_pages
                    get_books(page=st.session_state.page_num)
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No books found matching your criteria.")

def render_add_book_page():
    st.markdown("<h1 class='main-header'>Add New Book</h1>", unsafe_allow_html=True)
    
    with st.form("add_book_form"):
        title = st.text_input("Title")
        author = st.text_input("Author")
        year = st.number_input("Year", min_value=1000, max_value=datetime.now().year, value=datetime.now().year)
        genre = st.selectbox("Genre", [
            "Fiction", "Non-Fiction", "Science Fiction", "Fantasy", 
            "Mystery", "Thriller", "Romance", "Biography", 
            "History", "Science", "Self-Help", "Other"
        ])
        read = st.checkbox("I have read this book")
        
        submitted = st.form_submit_button("Add Book")
        
        if submitted:
            if not title or not author:
                st.error("Title and author are required.")
            else:
                success, message = add_book(title, author, year, genre, read)
                if success:
                    # Navigate to books page after adding
                    navigate_to("books")
                    st.rerun()
                else:
                    st.error(message)

def render_edit_book_page():
    st.markdown("<h1 class='main-header'>Edit Book</h1>", unsafe_allow_html=True)
    
    if not st.session_state.book_to_edit:
        st.error("No book selected for editing.")
        st.button("Back to Books", on_click=navigate_to, args=("books",))
        return
    
    book = st.session_state.book_to_edit
    book_id = book.get("_id")
    
    with st.form("edit_book_form"):
        title = st.text_input("Title", value=book.get("title", ""))
        author = st.text_input("Author", value=book.get("author", ""))
        year = st.number_input("Year", min_value=1000, max_value=datetime.now().year, value=book.get("year", datetime.now().year))
        genre = st.selectbox("Genre", [
            "Fiction", "Non-Fiction", "Science Fiction", "Fantasy", 
            "Mystery", "Thriller", "Romance", "Biography", 
            "History", "Science", "Self-Help", "Other"
        ], index=["Fiction", "Non-Fiction", "Science Fiction", "Fantasy", 
                 "Mystery", "Thriller", "Romance", "Biography", 
                 "History", "Science", "Self-Help", "Other"].index(book.get("genre", "Fiction")))
        read = st.checkbox("I have read this book", value=book.get("read", False))
        
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button("Update Book")
        
        with col2:
            cancel = st.form_submit_button("Cancel")
        
        if submitted:
            if not title or not author:
                st.error("Title and author are required.")
            else:
                success, message = update_book(book_id, title, author, year, genre, read)
                if success:
                    st.session_state.book_to_edit = None
                    navigate_to("books")
                    st.rerun()
                else:
                    st.error(message)
        
        if cancel:
            st.session_state.book_to_edit = None
            navigate_to("books")
            st.rerun()

# Main app logic
def main():
    # Display notification if exists
    display_notification()
    
    # Check if user is logged in
    if not st.session_state.token:
        render_login_page()
    else:
        # Render sidebar for navigation
        render_sidebar()
        
        # Render the appropriate page based on current_page
        if st.session_state.current_page == "dashboard":
            render_dashboard()
        elif st.session_state.current_page == "books":
            render_books_page()
        elif st.session_state.current_page == "add_book":
            render_add_book_page()
        elif st.session_state.current_page == "edit_book":
            render_edit_book_page()
        else:
            # Default to dashboard
            render_dashboard()

if __name__ == "__main__":
    main()