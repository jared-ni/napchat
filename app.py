from flask import Flask, render_template, make_response, redirect, request
import os
import pyrebase
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

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

""""
users = db.child("users").order_by_child("username").equal_to("hjw").get()
print(users.val())
for user in users.each():
  if user.val()['username'] == 'hjw':
    print("found")
"""

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
    
    userFound = False
    users = db.child("users").order_by_child("username").equal_to(username).get()

    for user in users.each():
      if user.val()['username'] == username:
        userFound = True
        if not check_password_hash(user.val()['hash'], password):
          warning = "wrong password"
          return render_template("login_alert.html", warning=warning)

    if not userFound:
      warning = "account doesn't exist"
      return render_template("login_alert.html", warning=warning)

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


@app.route("/register", methods=['GET', 'POST'])
def register():
  # push or set to database for sign up

  if request.method == 'POST':
    username = request.form.get("username")
    password = request.form.get("password")
    repassword = request.form.get("repassword")

    if not username or not password or not repassword:
      warning = "One or more fields are missing."
      return render_template("register_alert.html", warning=warning)
    elif password != repassword:
      warning = "Passwords do not match."
      return render_template("register_alert.html", warning=warning)
    
    # check if username exists
    users = db.child("users").order_by_child("username").equal_to(username).get()
    for user in users.each():
      if user.val()['username'] == username:
        warning = "username already exists."
        return render_template("register_alert.html", warning=warning)
    
    hash = generate_password_hash(password)

    data = {
      'username': username,
      'hash': hash,
    }
    db.child("users").push(data)

  return render_template("register.html")

@app.route("/newnap", methods=['GET', 'POST'])
@login_required
def newnap():

  if request.method == 'POST':
    date = request.form.get("date")
    start = request.form.get("start")
    end = request.form.get("end")

    print("date is " + date)
    print(start)
    print(end)

    return redirect("/")


  return render_template("newnap.html")
  
if __name__ == '__main__':
  app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
    