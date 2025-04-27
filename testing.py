# from pymongo import MongoClient
# client = MongoClient("mongodb://localhost:27017/")
# db = client["study_resources"]
# print(list(db["fs.files"].find()))
# from cryptography.fernet import Fernet

# # Generate a new Fernet key
# key = Fernet.generate_key()

# # Print the key (store it securely after generation)
# print(key.decode())

# import os
# from cryptography.fernet import Fernet

# # Get the key from environment variable
# MASTER_KEY = os.environ.get("FERNET_KEY")

# # Create a Fernet cipher object
# cipher = Fernet(MASTER_KEY)
# import sqlite3

# def create_table():
#     conn = sqlite3.connect("users.db")
#     c = conn.cursor()
#     c.execute('''CREATE TABLE IF NOT EXISTS users (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         username TEXT UNIQUE,
#         full_name TEXT,
#         email TEXT UNIQUE,
#         phone TEXT,
#         dob TEXT,
#         gender TEXT,
#         state TEXT,
#         city TEXT,
#         qualification TEXT,
#         optional_subject TEXT,
#         preparation_stage TEXT,
#         target_year TEXT,
#         password TEXT
#     )''')
#     conn.commit()
#     conn.close()

# # Call this once at the start of your code
# create_table()
# from pymongo import MongoClient

# # Connect to MongoDB
# client = MongoClient("mongodb://localhost:27017/")  # Update with your DB URL if different
# db = client["smart_prep"]  # Replace with your DB name
# collection = db["blogs"]  # Replace with your collection name

# # Delete all blog documents
# result = collection.delete_many({})

# # Check the number of deleted blogs
# print(f"{result.deleted_count} blogs deleted successfully.")

