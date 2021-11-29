from flask import Flask, render_template, make_response, redirect, request
import os
import pyrebase
from functools import wraps

# firebase configuration
firebaseConfig = {
  'apiKey': "AIzaSyBWNP6emxWHKVLzHpSh3mcrLehvFEWWnOI",
  'authDomain': "napchat-58702.firebaseapp.com",
  'databaseURL': "https://napchat-58702-default-rtdb.firebaseio.com/",
  'projectId': "napchat-58702",
  'storageBucket': "napchat-58702.appspot.com",
  'messagingSenderId': "284362631891",
  'appId': "1:284362631891:web:6c28e23af9f8e658294226",
  'measurementId': "G-8S27DG21PW"
}
firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()
auth = firebase.auth()
storage = firebase.storage()

# define login decoration
def login_required(f):
  """
  https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
  """
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if db.child("session").child("user_id").get().val() is None:
      return redirect("/login")
    return f(*args, **kwargs)
  return decorated_function


# config app
app = Flask(__name__)


@app.route("/")
@login_required
def index():
  print(db.child("session").child("user_id").get())
  return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():

  # clear session
  db.child("session").child("user_id").remove()

  # get username and password from form
  if request.method == "POST":
    username = request.form.get("username")
    password = request.form.get("password")
    try:
      auth.sign_in_with_email_and_password(username, password)
    except: 
      print("Invalid user or password. Try again")
      exit(0)
  
    #store username and password in firebase session
    db.child("session").update({'user_id': username})

    return redirect("/")

  return render_template("login.html")


@app.route("/logout")
def logout():
  """Log user out"""
  # Forget any user_id
  db.child("session").child("user_id").remove()
  # Redirect user to login form
  return redirect("/")


@app.route("/register", method=['GET', 'POST'])
def register():
  # push or set to database for sign up
  data = {
    'username': 'milkteadjTest',
    'password': '123456'
  }
  db.child("users").child("new").set(data)

  return render_template("register.html")

  
if __name__ == '__main__':
  app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
    