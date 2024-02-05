// Wait for the DOM to be fully loaded
$(document).ready(function() {
            // Form submission handling
            $('#bookForm').submit(function(event) {
                // Prevent the default form submission
                event.preventDefault();

                // Gather form data
                var author = $('#author').val();
                var bookName = $('#bookName').val();
                var genre = $('#genre').val();
                var purchaseDate = $('#purchaseDate').val();
                var price = $('#price').val();
                var publicationDate = $('#publicationDate').val();

                // Send an AJAX request to the server to add the book
                $.ajax({
                    type: 'POST',
                    url: '/add_book',
                    data: {
                        author: author,
                        bookName: bookName,
                        genre: genre,
                        purchaseDate: purchaseDate,
                        price: price,
                        publicationDate: publicationDate
                    },
                    success: function(response) {
                        // On success, update the book list
                        updateBookList();
                    },
                    error: function(error) {
                        console.error('Error:', error);
                    }
                });
            });

            // Function to update the book list
            function updateBookList() {
                $.get('/book_list', function(books) { 
                    // Clear the current book list
                    $('#bookList').empty();

                    // Loop through the received book data and append it to the book list
                    books.forEach(function(book) {
                        var bookItem = $('<a>')
                            .addClass('list-group-item list-group-item-action')
                            .text(book.author + ' - ' + book.book_name); // Display book author and name

                        $('#bookList').append(bookItem);
                    });
                });
            }

            // Initial load of book list on page load
            updateBookList();

            // Function to filter and display books based on selected genre
            window.showBooks = function() {
                var selectedGenre = document.getElementById("genre").value;
                var books = {
                    {
                        books | tojson
                    }
                };

                var bookTableBody = document.getElementById("bookTableBody");
                bookTableBody.innerHTML = '';


                for (var i = 0; i < books.length; i++) {
                    if (books[i].genre === selectedGenre) {
                        // Populate table rows based on the selected genre
                        var row = bookTableBody.insertRow();

                        // Create table cells and populate data
                        var authorCell = row.insertCell(0);
                        authorCell.innerHTML = books[i].author;

                        var bookNameCell = row.insertCell(1);
                        bookNameCell.innerHTML = books[i].book_name;

                        var genreCell = row.insertCell(2);
                        genreCell.innerHTML = books[i].genre;

                        var purchaseDateCell = row.insertCell(3);
                        purchaseDateCell.innerHTML = books[i].purchase_date;

                        var currency = books[i].currency; // Assuming you store the currency in your book object
                        var currencySymbol = currencySymbolMap[currency] || currency;

                        var priceCell = row.insertCell(4);
                        priceCell.innerHTML = currencySymbol + books[i].price; // Display price with currency symbol

                        var publicationYearCell = row.insertCell(5);
                        publicationYearCell.innerHTML = books[i].publication_year;

                        var actionsCell = row.insertCell(6);
                        var editButton = document.createElement("a");
                        editButton.href = "{{ url_for('edit_book', book_id='') }}" + books[i].id;
                        editButton.className = "btn btn-primary";
                        editButton.textContent = "Edit";
                        actionsCell.appendChild(editButton);

                        var deleteForm = document.createElement("form");
                        deleteForm.action = "{{ url_for('delete_book', book_id='') }}" + books[i].id;
                        deleteForm.method = "POST";
                        deleteForm.style.display = "inline";
                        actionsCell.appendChild(deleteForm);

                        var deleteButton = document.createElement("button");
                        deleteButton.type = "submit";
                        deleteButton.className = "btn btn-danger";
                        deleteButton.textContent = "Delete";
                        deleteButton.setAttribute("onclick", "return confirm('Are you sure you want to delete this book?')");
                        deleteForm.appendChild(deleteButton);
                    }
                }
            };
