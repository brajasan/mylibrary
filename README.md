# Library Management System

This is a Library Management System built with Streamlit and MySQL. It provides a user-friendly interface for managing books, users, loans, and reviews in a library setting.

## Features

- User authentication (login and signup)
- Book management (add, edit, remove books)
- Book borrowing and returning
- Book reviews and ratings
- Book search functionality
- Admin reports (book stats, most borrowed books, overdue books)
- User-specific book recommendations

## Prerequisites

- Python 3.7+
- MySQL Server

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  
   ```
   on Windows
   ```bash
   virtualenv venv
   venv\Scripts\activate
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your MySQL database:
   - Create a new MySQL database
   - Update the `.env` file with your MySQL credentials

5. Initialize the database:
   ```bash
   python init_db.py
   ```

## Usage

1. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. Open your web browser and go to `http://localhost:8501`

## Project Structure

- `app.py`: Main application file containing the Streamlit interface and core functionality
- `init_db.py`: Script to initialize the MySQL database and create necessary tables
- `.env`: Configuration file for database credentials (not included in the repository)

## Database Schema

The system uses the following tables:
- `users`: Stores user information
- `books`: Stores book information
- `categories`: Stores book categories
- `loans`: Tracks book loans
- `reviews`: Stores book reviews and ratings

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the [MIT License](LICENSE).
