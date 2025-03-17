from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, JWTManager, get_jwt_identity, get_jwt
from database import books_collection, users_collection
from bson import ObjectId
import bcrypt
import os
from dotenv import load_dotenv
import re
from datetime import datetime, timezone, timedelta

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Set JWT Secret Key
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")  
# Set token expiration (optional)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
jwt = JWTManager(app)

# Token blocklist for logout functionality
jwt_blocklist = set()

@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in jwt_blocklist

# Email validation function
def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

### ✅ User Registration Route
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.json
        if not data:
            return jsonify({"message": "No data provided"}), 400
            
        email = data.get("email")
        password = data.get("password")
        
        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400
            
        if not is_valid_email(email):
            return jsonify({"message": "Invalid email format"}), 400
            
        if len(password) < 8:
            return jsonify({"message": "Password must be at least 8 characters long"}), 400

        # Check if user already exists
        existing_user = users_collection.find_one({"email": email})
        if existing_user:
            return jsonify({"message": "User already exists!"}), 400

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # Store user in DB
        users_collection.insert_one({
            "email": email, 
            "password": hashed_password,
            "created_at": datetime.now(timezone.utc)
        })
        return jsonify({"message": "User registered successfully!"}), 201
    except Exception as e:
        return jsonify({"message": f"Registration error: {str(e)}"}), 500


### ✅ User Login Route
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        if not data:
            return jsonify({"message": "No data provided"}), 400
            
        email = data.get("email")
        password = data.get("password")
        
        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400

        # Find user in DB
        user = users_collection.find_one({"email": email})
        if not user:
            return jsonify({"message": "Invalid credentials"}), 401

        # Check password
        if bcrypt.checkpw(password.encode("utf-8"), user["password"]):
            access_token = create_access_token(identity=email)
            return jsonify({"token": access_token}), 200
        else:
            return jsonify({"message": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"message": f"Login error: {str(e)}"}), 500


### ✅ Protected Route (Only Authenticated Users)
@app.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    current_user = get_jwt_identity()
    return jsonify({"message": f"Welcome, {current_user}!"}), 200


### ✅ Logout Route (Token Invalidation)
@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    jwt_blocklist.add(jti)
    return jsonify({"message": "Logout successful!"}), 200


### ✅ CRUD Operations (Books)

# 📌 Add a New Book (Authenticated Users Only)
@app.route("/add_book", methods=["POST"])
@jwt_required()
def add_book():
    try:
        data = request.json
        current_user = get_jwt_identity()  # Get logged-in user

        if not data:
            return jsonify({"message": "No data received!"}), 400
            
        # Validate required fields
        required_fields = ["title", "author"]
        for field in required_fields:
            if field not in data or not data.get(field):
                return jsonify({"message": f"Field '{field}' is required"}), 400
                
        # Validate year is a number
        try:
            year = int(data.get("year", datetime.now().year))
            if year < 0 or year > datetime.now().year:
                return jsonify({"message": "Invalid year"}), 400
        except ValueError:
            return jsonify({"message": "Year must be a number"}), 400

        book = {
            "title": data.get("title"),
            "author": data.get("author"),
            "year": year,
            "genre": data.get("genre", "Fiction"),
            "read": data.get("read", False),
            "user": current_user,  # 👈 Store user email with book
            "created_at": datetime.now(timezone.utc)
        }

        result = books_collection.insert_one(book)
        return jsonify({
            "message": "Book added successfully!",
            "book_id": str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({"message": f"Error adding book: {str(e)}"}), 500


# 📌 Get All Books (Only for Logged-in User)
@app.route("/books", methods=["GET"])
@jwt_required()
def get_books():
    try:
        current_user = get_jwt_identity()
        
        # Add pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Limit per_page to prevent performance issues
        if per_page > 50:
            per_page = 50
            
        skip = (page - 1) * per_page
        
        # Get total count for pagination info
        total_books = books_collection.count_documents({"user": current_user})
        
        # Convert ObjectId to string for JSON serialization
        books = list(books_collection.find({"user": current_user}).skip(skip).limit(per_page))
        for book in books:
            book["_id"] = str(book["_id"])
            
        return jsonify({
            "books": books,
            "page": page,
            "per_page": per_page,
            "total": total_books,
            "pages": (total_books + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({"message": f"Error retrieving books: {str(e)}"}), 500


# 📌 Get a Book by ID (Only if it belongs to the logged-in user)
@app.route("/book/<book_id>", methods=["GET"])
@jwt_required()
def get_book_by_id(book_id):
    try:
        current_user = get_jwt_identity()
        
        # Validate ObjectId format
        if not ObjectId.is_valid(book_id):
            return jsonify({"message": "Invalid book ID format"}), 400
            
        book = books_collection.find_one({"_id": ObjectId(book_id), "user": current_user})
        
        if book:
            # Convert ObjectId to string for JSON serialization
            book["_id"] = str(book["_id"])
            return jsonify(book)
        else:
            return jsonify({"message": "Book not found or access denied!"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 📌 Update a Book (Only if it belongs to the logged-in user)
@app.route("/update_book/<book_id>", methods=["PUT"])
@jwt_required()
def update_book(book_id):
    try:
        current_user = get_jwt_identity()
        data = request.json
        
        if not data:
            return jsonify({"message": "No data provided"}), 400
            
        # Validate ObjectId format
        if not ObjectId.is_valid(book_id):
            return jsonify({"message": "Invalid book ID format"}), 400
            
        # Check if book exists and belongs to user
        existing_book = books_collection.find_one({"_id": ObjectId(book_id), "user": current_user})
        if not existing_book:
            return jsonify({"message": "Book not found or access denied"}), 404
            
        # Validate year if provided
        if "year" in data:
            try:
                year = int(data["year"])
                if year < 0 or year > datetime.now().year:
                    return jsonify({"message": "Invalid year"}), 400
            except ValueError:
                return jsonify({"message": "Year must be a number"}), 400
        
        # Build update document
        update_data = {}
        allowed_fields = ["title", "author", "year", "genre", "read"]
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
                
        if "year" in update_data:
            update_data["year"] = int(update_data["year"])
                
        update_data["updated_at"] = datetime.now(timezone.utc)

        result = books_collection.update_one(
            {"_id": ObjectId(book_id), "user": current_user},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return jsonify({"message": "Book updated successfully!"})
        else:
            return jsonify({"message": "No changes made to the book"}), 200
    except Exception as e:
        return jsonify({"message": f"Error updating book: {str(e)}"}), 500


# 📌 Delete a Book (Only if it belongs to the logged-in user)
@app.route("/delete_book/<book_id>", methods=["DELETE"])
@jwt_required()
def delete_book(book_id):
    try:
        current_user = get_jwt_identity()
        
        # Validate ObjectId format
        if not ObjectId.is_valid(book_id):
            return jsonify({"message": "Invalid book ID format"}), 400
            
        # Check if book exists and belongs to user before deleting
        existing_book = books_collection.find_one({"_id": ObjectId(book_id), "user": current_user})
        if not existing_book:
            return jsonify({"message": "Book not found or access denied"}), 404
            
        result = books_collection.delete_one({"_id": ObjectId(book_id), "user": current_user})
        
        if result.deleted_count > 0:
            return jsonify({"message": "Book deleted successfully!"})
        else:
            return jsonify({"message": "Book not found or access denied!"}), 404
            
    except Exception as e:
        return jsonify({"message": f"Error deleting book: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)