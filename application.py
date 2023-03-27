import os
import json
import time
import base64

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from helpers import info_pics, info_descr, randomise, randomise_2, avg_interval, img_generator
from datetime import datetime

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///gaitquiz.db")

# Configure session
random_key = str(os.urandom(8))
app.config['SECRET_KEY'] = random_key
app.config['SESSION_TYPE'] = 'filesystem'
app.config["SESSION_COOKIE_NAME"] = "session"
app.config["SESSION_PERMANENT"] = False
Session(app)

# Generate random session id
@app.before_first_request
def id():
    id = str(os.urandom(8))
    return id

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"

    return response

# Generate copy of the generated random id, so that id stays the same during the session
def id_saver(id=id()):
    return id

# Index contains variables that refer to locations of stored images
@app.route("/", methods=["GET", "POST"])
def index():

    index = url_for('static', filename='index2.jpg')
    redline = url_for('static', filename='redline.jpg')
    whichleg = url_for('static', filename='whichleg.jpg')
    logo_img_small = url_for('static', filename='logo-geknipt.png')
    return render_template("index.html", index=index, logo_img_small=logo_img_small, redline=redline, whichleg=whichleg)


@app.route("/picture-quiz", methods=["GET", "POST"])
def picture_quiz(id=id_saver()):

    time = datetime.now() # Time represents the timestamp at the moment the user clicks a button with an answer
    info_temp = info_pics() # Info_temp gets information about the pictures from the helpers file. Every picture is linked to a correct answer
    random_id = randomise() # Random_id uses a function from the helpers file to generate a random id number to generate a question with
    correct_answer = info_temp[random_id] # The random id is linked to the information from the info function, which defines the correct answer
    file = str(random_id) + ".JPG" # File represents the name of the file we want to retrieve from the static folder, containing the image
    quiz_img = url_for('static', filename=file)
    logo_img = url_for('static', filename='logo-geknipt.png')


    id = random_key


    try:
        # Intervals is a variable that takes the timestamps from the user's last three answers
        intervals = db.execute("SELECT time FROM results WHERE id=? AND picdesc=? ORDER BY answer_id desc LIMIT 3", id, "pic")
        # Avg_time takes the aforementioned variable 'intervals', and passes it through a function from the helpers file. The result is the average time in seconds
        avg_time = avg_interval(intervals)
        # The progress bar on the html page has a width of 150. A full bar represents the highest speed. I subtract my average time, multiplied by ten for added sensitivity
        score = 150 - (avg_time * 10)
    except:
        # It's impossible to retrieve information about the average time if less than three answers have been given by the user so far.
        avg_time = "Please answer more questions first"
        score = 0

    if request.method == "POST":
        """ The button click on the html page triggers an event that is contained in the java file. The value from the html button is compared to the correct answer.
            The result from the comparison that happens in the java file is sent here by means of a JSON request. User_answer is a variable that contains a string.
            The string can either be 'correct', or 'incorrect'.
        """
        user_answer = request.get_json()["answer"]
        # After user_answer is defined ('correct' or 'incorrect'), all the required information is added to the database
        db.execute("INSERT INTO results (correct, id, time, picdesc) VALUES(?, ?, ?, ?)", user_answer, id, time, "pic")
        return render_template("quiz.html", correct_answer=correct_answer, quiz_img=quiz_img)

    return render_template("quiz.html", correct_answer=correct_answer, quiz_img=quiz_img, logo_img=logo_img, score=score)

@app.route("/description-quiz", methods=["GET", "POST"])
def description_quiz(id=id_saver()):

    time = datetime.now() # Time represents the timestamp at the moment the user clicks a button with an answer
    info_temp = randomise_2() # Info_temp gets information about the questions from the helpers file. Every question is linked to a correct answer

    for var in info_temp:  # Info_temp contains a tuple. The key represents the question and the value represents the answer
        question = info_temp[0]
        correct_answer = info_temp[1]

    logo_img = url_for('static', filename='gaitquiz-logo-small.png') # Logo_img is a picture in the static folder that I need for the html page
    image_memory = img_generator(question) # Img_generator is a function from the helpers file that takes a background and adds text to it. The added text is our question.

    try:
        # Intervals is a variable that takes the timestamps from the user's last three answers
        intervals = db.execute("SELECT time FROM results WHERE id=? AND picdesc=? ORDER BY answer_id desc LIMIT 3", id, "desc")
        # Avg_time takes the aforementioned variable 'intervals', and passes it through a function from the helpers file. The result is the average time in seconds
        avg_time = avg_interval(intervals)
        # The progress bar on the html page has a width of 150. A full bar represents the highest speed. I subtract my average time, multiplied by ten for added sensitivity
        score = 150 - (avg_time * 7)
    except:
        # It's impossible to retrieve information about the average time if less than three answers have been given by the user so far.
        avg_time = "Please answer more questions first"
        score = 0

    if request.method == "POST":
        """ The button click on the html page triggers an event that is contained in the java file. The value from the html button is compared to the correct answer.
        The result from the comparison that happens in the java file is sent here by means of a JSON request. User_answer is a variable that contains a string.
        The string can either be 'correct', or 'incorrect'.
        """
        user_answer = request.get_json()["answer"]
        # After user_answer is defined ('correct' or 'incorrect'), all the required information is added to the database
        db.execute("INSERT INTO results (correct, id, time, picdesc) VALUES(?, ?, ?, ?)", user_answer, id, time, "desc")
        # Image_memory is a variable that contains an encoded image. Before passing it to the html page, it is decoded
        return render_template("quiz.html", id=id, correct_answer=correct_answer, question=question, img=image_memory.decode('utf-8'))

    return render_template("description_quiz.html", correct_answer=correct_answer, question=question, logo_img=logo_img, score=score,
    img=image_memory.decode('utf-8'))


@app.route("/mobilewarning", methods=["GET", "POST"])
def mobilewarning(id=id_saver()):
    logo_img_small = url_for('static', filename='gaitquiz-logo-small.png')
    return render_template("mobilewarning.html", logo_img_small=logo_img_small)

if __name__ == "__main__":
    app.run()#(debug=False, host='0,0,0,0')








