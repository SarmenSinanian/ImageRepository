from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from os.path import exists
import sqlite3
import base64
import os

current_directory = os.getcwd()

app = Flask(__name__)


def get_cursor():
    sqliteConnection = sqlite3.connect("ImageRepository.db")
    cursor = sqliteConnection.cursor()
    return sqliteConnection, cursor


"""Initialize the sqlite database and fill up the `products` table with sample data."""


def initialize_db():
    db_exists = exists(
        f"{current_directory}\ImageRepository.db")

    if db_exists:
        print('DB DOES EXIST')

    if not db_exists:
        print('DB DOES NOT EXIST')
        # Create initial table
        sqliteConnection = sqlite3.connect('ImageRepository.db')
        cursor = sqliteConnection.cursor()
        cursor.execute('''CREATE TABLE photos
                        (id INTEGER PRIMARY KEY, photo BLOB NOT NULL);''')
        sqliteConnection.commit()
    print("Initialized database")


def convert_to_binary_data(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        blobData = file.read()
    return blobData


def insert_blob(photo_id, photo):
    try:
        (sqliteConnection, cursor) = get_cursor()
        print("Connected to SQLite")
        sqlite_insert_blob_query = """ INSERT INTO photos
                                  (id, photo) VALUES ( ?, ?)"""
        photo = convert_to_binary_data(photo)
        # Convert data into tuple format
        data_tuple = (photo_id, photo)
        cursor.execute(sqlite_insert_blob_query, data_tuple)
        sqliteConnection.commit()
        print("Image and file inserted successfully as a BLOB into a table")
        cursor.close()
        print("The sqlite connection is closed")
    except sqlite3.Error as error:
        print("Failed to insert blob data into sqlite table", error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print("The sqlite connection is closed")


@app.route("/")
def home_page():
    (sqliteConnection, cursor) = get_cursor()
    print("Connected to SQLite")
    cursor.execute("SELECT rowid, * FROM photos")
    rows = cursor.fetchall()
    print("Retrieved %d database entries" % len(rows))
    # For HTML Display
    images = []
    for row in rows:
        images.append({
            "id": row[1],
            "image": row[2].decode()
        })
    cursor.close()
    return render_template("index.html", images=images)


@app.route("/add_photo/", methods=['POST'])
def add_photo():
    pics = request.files['files']
    pic_list = request.files.getlist('files')
    if not pics:
        return "No pic uploaded!", 400
    filename = secure_filename(pics.filename)
    mimetype = pics.mimetype
    if not filename or not mimetype:
        return "Bad upload!", 400
    (sqliteConnection, cursor) = get_cursor()
    print("Connected to SQLite")
    # Grabbing final row from db for ID numbering reasons
    cursor.execute("SELECT id FROM photos ORDER BY id DESC LIMIT 1")
    finalEntryID = cursor.fetchone()
    #
    for count, i in enumerate(pic_list, 1):
        photoBytes = i.read()
        photoData = base64.b64encode(photoBytes)
        if finalEntryID is None:
            finalEntryID = [0]
        data_tuple = (count + finalEntryID[0], photoData)
        sqlite_addPhoto_query = """ INSERT INTO photos
                                          (id, photo) VALUES ( ?, ?)"""
        cursor.execute(sqlite_addPhoto_query, data_tuple)
    sqliteConnection.commit()
    print("Images inserted successfully as a BLOB into a table")
    cursor.close()
    # return 'Image(s) Uploaded! Press the back button and refresh the page.', 200
    return render_template("add_photo.html", message="Image(s) Uploaded! Press the 'Main Page' button (or your browser's"
                                                    " 'Back' button) and refresh the page."), 200


@app.route("/delete_pic/<image_id>")
def delete_pic(image_id):
    if not image_id:
        return render_template("delete_pic.html", message="Invalid image ID!"), 400

    (sqliteConnection, cursor) = get_cursor()

    cursor.execute("DELETE FROM photos WHERE id = ?", (image_id,))
    sqliteConnection.commit()
    cursor.execute("VACUUM")

    sqliteConnection.commit()
    return render_template("delete_pic.html", message="Image deletion successful!"), 200


# @app.route("/image/:id", methods=['GET'])
# def image():


@app.route("/reset")
def reset():
    (sqliteConnection, cursor) = get_cursor()
    cursor.execute("DROP TABLE IF EXISTS photos")
    cursor.execute("VACUUM")
    cursor.execute('''CREATE TABLE photos
                    (id INTEGER PRIMARY KEY, photo BLOB NOT NULL);''')
    sqliteConnection.commit()
    cursor.close()
    return render_template("reset.html", message="Database reset. Press the 'Main Page' button (or your browser's 'Back"
                                                 "' button) and refresh the page."), 200


if __name__ == '__main__':
    initialize_db()
    app.run(debug=False)
