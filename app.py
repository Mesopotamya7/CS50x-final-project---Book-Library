import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, url_for, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import login_required, apology

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure database

db = SQL("sqlite:///books.db")

# Create the users table to store username and password
users_table = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    hash TEXT NOT NULL
);
"""
db.execute(users_table)

# Create books table to hold all user data besides username and password

books_table = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author TEXT NOT NULL,
    book_name TEXT NOT NULL,
    genre TEXT NOT NULL,
    purchase_date DATE NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    publication_year INTEGER NOT NULL,
    ISBN TEXT,
    user_id INTEGER,
    action TEXT,
    details TEXT,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    book_gift INTEGER DEFAULT 0,
    currency TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
"""
db.execute(books_table)

# Specifying directivness for caching behavior

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Decorator to define the root url of the web application

@app.route("/")
@login_required
def index():
    """Redirect to login page if not logged in; othwewise show shelves of books"""
    if session.get("user_id") is None:
        return render_template("login.html")
    else:
        return redirect(url_for("book_library"))

# Decorator to handle the url for registration process

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check if username or password are empty
        if not username or not password or not confirmation:
            return apology("Username or Password is missing")

        # Check if password matches confirmation
        if password != confirmation:
            return apology("Passwords do not match")

        # Check if username already exists in db
        existing_user = db.execute("SELECT * FROM users WHERE username = ?", (username,))
        if existing_user:
            return apology("Username already exists")

        # Insert new user in db
        hashed_password = generate_password_hash(password)
        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            username,
            hashed_password,
        )

        # Redirect to login page after succesfull registration
        return redirect("/login")
    else:
        return render_template("register.html")

# Decorator to define the url for login page and logic

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    if request.method == "POST":
        # Make sure username was submitted
        if not request.form.get("username"):
            apology_message = "Must provide username"
            return render_template("apology.html", top=400, bottom=apology_message)

        # Make sure the password was submitted
        if not request.form.get("password"):
            apology_message = "Must provide password"
            return render_template("apology.html", top=400, bottom=apology_message)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Make sure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            apology_message = "Invalid username and/or password"
            return render_template("apology.html", top=400, bottom=apology_message)

        # Store the user id in the session
        session["user_id"] = rows[0]["id"]
        print("User ID storen in session: ", session["user_id"])  # Debug statement

        # Redirect to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

# Decorator to define the url for logout page and logic

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/shelves")
def shelves():
    """Show shelves of books for the logged user"""
    # Get user id from the session
    user_id = session["user_id"]

    # Get distinct genres specific to the logged user from the books for shelves.html
    genres = db.execute(
        "SELECT DISTINCT genre FROM books WHERE user_id = ? AND action != 'Deleted' ORDER by genre",
        user_id,
    )

    # Get books specific to the logged user from the book_library route
    books = db.execute(
        "SELECT * FROM books WHERE user_id = ? AND action != 'Deleted' ORDER BY genre",
        user_id,
    )

    return render_template(
        "shelves.html", genres=[genre["genre"] for genre in genres], books=books
    )

# Decorator to define and process the url for add_book page

@app.route("/add_book", methods=["GET", "POST"])
@login_required
def add_book():
    if request.method == "POST":
        author = request.form.get("author")
        book_name = request.form.get("book_name")
        genre = request.form.get("genre")
        purchase_date = request.form.get("purchase_date")
        price = request.form.get("price")
        book_gift = request.form.get("book_gift")

        # Set default value if book_digit is not provided or not a valid number
        if book_gift is None or not book_gift.isdigit():
            # Handle the case when book_gift is not present in the form, 0 is not present
            book_gift = 0
        else:
            book_gift = int(book_gift)

        # Get the user id from the session
        user_id = session["user_id"]

        # Check if the book already exists in the database
        existing_book = db.execute(
            """
            SELECT * FROM books
            WHERE LOWER(author) = LOWER(?) AND LOWER(book_name) = LOWER(?)
            AND LOWER(genre) = LOWER(?) AND user_id = ? AND action != 'Deleted'
            """,
            author,
            book_name,
            genre,
            user_id,
        )

        # If book exists already, return apology message
        if existing_book:
            apology_message = "Book already exists"
            return render_template("apology.html", top=400, bottom=apology_message)

        # Add to the 'books' table
        db.execute(
            "INSERT INTO books (author, book_name, genre, purchase_date, price, book_gift, user_id, action, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            author,
            book_name,
            genre,
            purchase_date,
            price,
            book_gift,
            user_id,
            "Added",
            f"Added book: {book_name} by {author}",
        )

        # Flash a success message
        flash("Your book was successfully added", "success")
        # Redirect to the book library page or any desired page after adding a book
        return redirect(url_for("book_library"))

    # Handle GET request (or any other method)
    return render_template("add_book.html")

# Decorator to define and process the url for edit page

@app.route("/edit_book/<book_id>", methods=["GET", "POST"])
@login_required
def edit_book(book_id):
    # Check if book_id is a valid intenger
    try:
        book_id = int(book_id)
    except ValueError:
        # Handle the case when book_id is not a valid intenger
        flash("Invalid book ID", "error")
        return redirect(url_for("shelves"))

    # Identify user

    user_id = session.get("user_id")

    # Get book details based on book id and user id from books table
    book = db.execute(
        "SELECT * FROM books WHERE id = ? AND user_id = ?", book_id, user_id
    )

    # Check if the book exists and user has access to edit
    if not book:
        flash("Book not found or unauthorized access", "error")
        return redirect(url_for("shelves"))

    book = book[0] if book else None  # Extract the book if found

    if request.method == "POST":
        # Handle updating book details based on the submitted form data
        updated_author = request.form.get("author")
        updated_book_name = request.form.get("book_name")
        updated_genre = request.form.get("genre")
        updated_purchase_date = request.form.get("purchase_date")
        updated_price = request.form.get("price")
        updated_book_gift = request.form.get("book_gift")

        # Get the updated_book_gift value from the form
        updated_book_gift = request.form.get("book_gift")

        # Convert the updated_book_gift to an integer (0 or 1)
        updated_book_gift = 1 if updated_book_gift else 0

        # Update the book details in the books table
        db.execute(
            """
            UPDATE books
            SET author = ?, book_name = ?, genre = ?,
                purchase_date = ?, price = ?, book_gift = ?,
                action = ?
                WHERE id = ? AND user_id = ?
            """,
            updated_author,
            updated_book_name,
            updated_genre,
            updated_purchase_date,
            updated_price,
            updated_book_gift,  # Update the book_gift value
            "Updated",
            book_id,
            user_id,
        )

        # Flash a success message and redirect to shelves after updating book
        flash("Book successfully updated!", "success")
        return redirect(url_for("shelves"))

    # Render the edit book form with the book details for GET request
    return render_template("edit_book.html", book=book)

# Decorator to define the deletion process of books

@app.route("/delete_book/<book_id>", methods=["POST", "DELETE"])
@login_required
def delete_book(book_id):
    try:
        book_id = int(book_id)
    except ValueError:
        # Handle the case when book_id is not a valid intenger
        flash("Invalid book ID", "error")
        return redirect(url_for("shelves"))

    if request.method in ["POST", "DELETE"]:
        user_id = session["user_id"]

        # Check if the book exists for existing user
        book = db.execute(
            "SELECT * FROM books WHERE id = ? AND user_id = ?", book_id, user_id
        )
        if not book:
            flash("Book not found or unauthorized access", "error")
            return redirect(url_for("book_library"))

        # Mark the book as deleted by updating the action column
        db.execute(
            "UPDATE books SET action = ?, details = ?, date_created = ? WHERE id = ? AND user_id = ?",
            "Deleted",
            f"Deleted book: {book[0]['book_name']} by {book[0]['author']}",
            datetime.now(),
            book_id,
            user_id,
        )

        # Display message and return

        flash("Book deleted succesfully!", "success")
        return redirect(url_for("book_library"))
    else:
        # Handle GET request if needed
        flash("Book not found or unauthorized access", "error")
        return redirect(url_for("book_library"))

# Decorator to define book_library page

@app.route("/book_library")
@login_required
def book_library():
    # Get the user id from the session
    user_id = session["user_id"]

    # Fetch book list from the database including status (deleted or existing)
    books = db.execute(
        """
        SELECT *,
        CASE
            WHEN book_gift = 1 THEN 'Received as gift'
            ELSE price || ' ' || currency
        END AS display_price
        FROM books
        WHERE user_id = ? AND action != 'Deleted'
        """,
        user_id,
    )

    existing_books = [
        book for book in books if book.get("action") in ("Added", "Updated")
    ]

    return render_template("book_library.html", books=existing_books)

# Decorator to define overview page

@app.route("/overview")
@login_required
def book_overview():
    # Get the user id from the session
    user_id = session["user_id"]

    # Fetch book statistics from the database
    total_books_row = db.execute(
        "SELECT COUNT(*) as total FROM books WHERE user_id = ? AND action != 'Deleted'",
        user_id,
    )

    # Calculate total_books based on the fetched data
    total_books = total_books_row[0]["total"] if total_books_row else 0

    # Calculate favorite genre
    favorite_genre_row = db.execute(
        """
        SELECT genre, COUNT(genre) as genre_count
        FROM books
        WHERE user_id = ? AND action != 'Deleted'
        GROUP BY genre
        ORDER BY genre_count DESC
        LIMIT 1
        """,
        user_id,
    )

    favorite_genre = favorite_genre_row[0]["genre"] if favorite_genre_row else None

    # Find the most expensive book
    most_expensive_book_query = db.execute(
        """
        SELECT author, book_name, price
        FROM books
        WHERE price IS NOT NULL
        AND price != ''
        AND book_gift = 0
        AND user_id = ?
        AND action != 'Deleted'
        ORDER BY price DESC
        LIMIT 1
        """,
        user_id,
    )

    most_expensive_book = (
        most_expensive_book_query[0] if most_expensive_book_query else None
    )
    #IF the most expensive book is deleted, fetch the next most expensive book
    if most_expensive_book:
        if most_expensive_book.get("price") is None:
            next_expensive_book_query = db.execute(
            """
            SELECT author, book_name, price
            FROM books
            WHERE price IS NOT NULL
            AND price != ''
            AND user_id = ?
            AND action != 'Deleted'
            AND id != ?
            ORDER BY price DESC
            LIMIT 1
            """,
            user_id,
    most_expensive_book["id"],
            )

            next_expensive_book = (
                next_expensive_book_query[0] if next_expensive_book_query else None
            )

            if next_expensive_book:
                most_expensive_book = next_expensive_book

    # Calculate the total amount spent on books
    total_amount_paid_row = db.execute(
        """
        SELECT SUM(price) as total_paid
        FROM books
        WHERE user_id = ? and action != 'Deleted' AND price IS NOT NULL
        """,
        user_id,
    )

    total_amount_paid = (
        total_amount_paid_row[0]["total_paid"] if total_amount_paid_row else None
    )

    # Find the oldest purchased book
    oldest_purchased_book_row = db.execute(
        """
        SELECT author, book_name, purchase_date, price
        FROM books
        WHERE user_id = ?
        AND action != 'Deleted'
        AND purchase_date IS NOT NULL
        AND purchase_date != ''
        AND price IS NOT NULL
        AND price != ''
        AND book_gift = 0
        ORDER BY purchase_date ASC
        LIMIT 1
        """,
        user_id,
    )

    oldest_purchased_book = (
        oldest_purchased_book_row[0] if oldest_purchased_book_row else None
    )

    # Get info on most popular author
    most_popular_author_row = db.execute(
        """
        SELECT author, COUNT(author) as author_count
        FROM books
        WHERE user_id = ? AND action != 'Deleted'
        GROUP BY author
        ORDER BY author_count DESC
        LIMIT 1
        """,
        user_id,
    )

    most_popular_author = (
        most_popular_author_row[0]["author"] if most_popular_author_row else None
    )

    # Calculate the percentage of books received as gifts and their percentage
    total_gifted_books_row = db.execute(
        "SELECT COUNT(*) AS total_gifted FROM books WHERE user_id = ? AND book_gift = 1 AND action != 'Deleted'",
        user_id,
    )
    total_gifted_books = (
        total_gifted_books_row[0]["total_gifted"] if total_gifted_books_row else 0
    )

    # Calculate total number of purchased books
    total_purchased_books_row = db.execute(
        "SELECT COUNT(*) AS total_purchased FROM books WHERE user_id = ? AND book_gift = 0 AND action != 'Deleted'",
        user_id,
    )

    total_purchased_books = (
        total_purchased_books_row[0]["total_purchased"]
        if total_purchased_books_row
        else 0
    )

    # Calculate percentage of books received as gits
    book_gifts_percentage = (
        round((total_gifted_books / total_books) * 100, 2) if total_books > 0 else 0
    )

    # Calculate the percentage of purchased books
    books_purchased = (
        round((total_purchased_books / total_books) * 100, 2) if total_books > 0 else 0
    )

    # Find the newest book
    newest_book_row = db.execute(
        """
        SELECT author, book_name, purchase_date
        FROM books
        WHERE user_id = ? AND action != 'Deleted' AND purchase_date IS NOT NULL
        ORDER BY purchase_date DESC
        LIMIT 1
        """,
        user_id,
    )

    newest_book = newest_book_row[0] if newest_book_row else None

    # Render the template with calculated statistics
    return render_template(
        "book_overview.html",
        total_books=total_books,
        favorite_genre=favorite_genre,
        most_expensive_book=most_expensive_book,
        total_amount_paid=total_amount_paid,
        newest_book=newest_book,
        oldest_purchased_book=oldest_purchased_book,
        most_popular_author=most_popular_author,
        book_gifts_count=total_gifted_books,
        books_purchased=books_purchased,
        book_gifts_percentage=book_gifts_percentage,
    )

# Decorator to define contact page

@app.route("/contact")
@login_required
def contact():
    return render_template("contact.html")
