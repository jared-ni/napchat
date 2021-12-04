import datetime
from flask import Flask, render_template, make_response, redirect, request, session
import os
import pyrebase
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date, time
import requests
import json
import calendar

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
# storage = firebase.storage()

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
    if 'username' not in session:
      return redirect("/login")
    return f(*args, **kwargs)
  return decorated_function

# config app
app = Flask(__name__)

# set secret key for flask session
app.secret_key = db.child("session").child("secret_key").get().val()

@app.route("/")
@login_required
def index():
  
  year = 2020
  month = 12
  # first day determines the number of blank spaces to add
  weekdays = calendar.weekheader(3).split()
  #first_day = datetime.datetime(year, month, 1).weekday() #get day of the week (sun = 6)
  days = list(calendar.monthrange(year, month))
  if days[0] == 6:
    days[0] = -1
  
  # date list
  myDays = []
  for i in range(days[0] + 1):
    myDays.append("-")
  for i in range(1, days[1] + 1):
    myDays.append(str(i))
  for i in range(len(myDays), 35):
    myDays.append("-")

  # convert month to letter name
  month_name = calendar.month_name[month]

  # get records and store in 2d list
  print(session['username'])
  records = db.child("sleepTracker").order_by_child("username").equal_to(session['username']).get()
  print(records)
  
  myRecords = []
  for record in records.each():
    dateRecord = []
    dateRecord.append(record.val()['date'])
    dateRecord.append(record.val()['hours'])
    myRecords.append(dateRecord)

  print(myRecords)

  # Must sort with date's order and compare each date's hour to desired hours. 
  streak = 1
  sortedRecords = sorted(myRecords, key = lambda l:l[0], reverse=True)
  
  # calculate streak
  for i in range(len(sortedRecords) - 1):
    time_cur = datetime.datetime.strptime(sortedRecords[i][0], "%Y-%m-%d")
    time_prev = datetime.datetime.strptime(sortedRecords[i+1][0], "%Y-%m-%d")
    day_delta = str(time_cur - time_prev)[0:5]
    if day_delta != "1 day":
      break
    else:
      streak += 1
  # print(str(streak) + " streak!!!")

  # calculate 

  return render_template("index.html", weekdays=weekdays, myDays=myDays, year=year, month=month_name, streak=streak, myRecords=myRecords)


@app.route("/login", methods=["GET", "POST"])
def login():

  # clear login 
  session.pop('username', None)

  # get username and password from form
  if request.method == "POST":
    username = request.form.get("username")
    password = request.form.get("password")
    
    try:
      auth.sign_in_with_email_and_password(username, password)
      session['username'] = username
    except requests.HTTPError as e:
      error_json = e.args[1]
      error = json.loads(error_json)['error']['message']
      if error == "INVALID_PASSWORD":
        warning = "Invalid password. Try again."
      elif error == "INVALID_EMAIL":
        warning = "Invalid email. Try again."
      else:
        warning = "Could not log in with the provided information. Try again."
      return render_template("login_alert.html", warning=warning)
    
    return redirect("/")

  return render_template("login.html")


@app.route("/logout")
def logout():
  """Log user out"""
  # Forget any user_id
  session.pop('username', None)
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
    try:
      user = auth.create_user_with_email_and_password(email=username, password=password)
      return redirect("/")
    except requests.HTTPError as e:
      error_json = e.args[1]
      error = json.loads(error_json)['error']['message']
      if error == "EMAIL_EXISTS":
        warning = "An account already exists for this email address."
      elif error == "WEAK_PASSWORD : Password should be at least 6 characters" or error == "WEAK_PASSWORD":
        warning = "Password should be at least 6 characters long."
      elif error == "INVALID_EMAIL":
        warning = "please provide a valid email address"
      return render_template("register_alert.html", warning=warning)

  return render_template("register.html")

@app.route("/newnap", methods=['GET', 'POST'])
@login_required
def newnap():
  
  if request.method == 'POST':
    date = request.form.get("date") # formatted: 2021-11-12
    start = request.form.get("start") #formated: 20:19
    end = request.form.get("end") #formated: 07:18

    # before 12:00 am:
    start_arr = list(map(int, start.split(":")))
    end_arr = list(map(int, end.split(":")))

    # print(start_arr)
    # print(end_arr)
    # print("--------------------")

    # add the minutes together first, then hours
    if end_arr[0] == start_arr[0]:
      minutes = end_arr[1] - start_arr[1]
    else:
      minutes = int(end_arr[1]) + (60 - int(start_arr[1]))
      start_arr[0] += 1
    
    # print(str(minutes) + " minutes")
    
    hours = int(end_arr[0]) - int(start_arr[0])
    print(start_arr[0])
    print(end_arr[0])
    # print(str(hours) + " hours")

    if hours < 0:
      hours += 24
    hours += round(minutes/60, 1)
    # print(str(hours) + " hours updated")
    # print("----------------------------------------")

    username = session["username"]
    track = db.child("sleepTracker").order_by_child("username").equal_to(username).order_by_child("date").equal_to(date).get()
    # empty list is False, empty dict is None
    if not track.val():
      data = {
        'date': date,
        'hours': hours,
        'username': username
      }
      db.child("sleepTracker").push(data)
    else:
      for day in track.each():
        existing_hours = day.val()['hours']
        db.child("sleepTracker").child(day.key()).update({'hours': existing_hours + hours})

    return redirect("/")

  today = datetime.date.today()
  week_ago = today - datetime.timedelta(days=7)

  return render_template("newnap.html", today=today, week_ago=week_ago)
  
if __name__ == '__main__':
  app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
    