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
  
  year = datetime.datetime.now().year
  month = datetime.datetime.now().month
  today = str(date.today())
  today_day = int(today[8:])
  goal = 8

  # user information and retrieve sleep goal
  user_records = db.child("users").order_by_child("username").equal_to(session['username']).get()
  for record in user_records.each():
    try:
      goal = float(record.val()['goal'])
      default_goal = False
    except:
      goal = 8
      default_goal = True

  
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
  records = db.child("sleepTracker").order_by_child("username").equal_to(session['username']).get()
  
  myRecords = []
  for record in records.each():
    dateRecord = []
    dateRecord.append(record.val()['date'])
    dateRecord.append(record.val()['hours'])
    myRecords.append(dateRecord)

  # Must sort with date's order and compare each date's hour to desired hours. 
  streak = 0
  sortedRecords = sorted(myRecords, key = lambda l:l[0], reverse=True)

  # calculate streak
  time_now = datetime.datetime.strptime(today, "%Y-%m-%d")
 
  if not sortedRecords:
    streak = 0
  elif time_now == datetime.datetime.strptime(sortedRecords[0][0], "%Y-%m-%d") and sortedRecords[0][1] >= goal:
    streak += 1
    for i in range(len(sortedRecords) - 1):
      time_cur = datetime.datetime.strptime(sortedRecords[i][0], "%Y-%m-%d")
      time_prev = datetime.datetime.strptime(sortedRecords[i+1][0], "%Y-%m-%d")
      day_delta = str(time_cur - time_prev)[0:5]
      if day_delta == "1 day" and sortedRecords[i+1][1] >= goal:
        streak += 1
      else:
        break

  # calculate whether each day in the month meets the required hours
  monthColor = []
  for i in range(days[0] + 1):
    monthColor.append(False)

  for i in range(1, days[1] + 1):
    dayString = str(year) + "-" + str(month) + "-"
    if i < 10:
      dayString += "0" + str(i)
    else: 
      dayString += str(i)

    added = False
    for record in sortedRecords:
      if record[0] == dayString and record[1] >= goal:
        monthColor.append(True)
        added = True
        break
    if not added:
      monthColor.append(False)

  # loop through the user record
  for record in user_records.each():
    try:
      name = record.val()['name']
    except:
      name = "not set"
    try: 
      birthday = record.val()['birthday']
    except:
      birthday = "not set"

    # check if goal was defaulted
    if default_goal:
      goal = "not set (defaulted to 8 hours / day)"
    else:
      goal = str(goal) + " hours / day"

    # process age
    if birthday == "not set":
      age = "not set"
    else:
      today = str(date.today())
      today = datetime.datetime.strptime(today, "%Y-%m-%d")
      birthday = datetime.datetime.strptime(birthday, "%Y-%m-%d")
      day_delta = today - birthday
      day_delta = day_delta.days
      age = day_delta // 365

    # recommend sleep hours based on age
    if not isinstance(age, int):
      recommended = "8+ hours (age not set)"
    elif age <= 12:
      recommended = "9-12 hours / day"
    elif age <= 18:
      recommended = "8-10 hours / day"
    elif age <= 60:
      recommended = "7+ hours / day"

  return render_template("index.html", 
    weekdays=weekdays, 
    myDays=myDays, 
    year=year, 
    month=month_name, 
    streak=streak, 
    myRecords=myRecords, 
    monthColor=monthColor, 
    today_day=today_day,
    name=name, age=age, goal=goal, recommended=recommended
  )


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


@app.route("/profile")
def profile():

  # retreive user information
  records = db.child("users").order_by_child("username").equal_to(session['username']).get()
  for record in records.each():
    try:
      name = record.val()['name']
    except:
      name = "not set"
    try: 
      birthday = record.val()['birthday']
      # process age
      today = str(date.today())
      today = datetime.datetime.strptime(today, "%Y-%m-%d")
      birthday = datetime.datetime.strptime(birthday, "%Y-%m-%d")
      day_delta = today - birthday
      day_delta = day_delta.days
      age = day_delta // 365
    except:
      age = "not set"
    try:
      goal = str(record.val()['goal'])
      goal += " hours / day"
    except:
      goal = "not set (default = 8 hours)"
    

    email = session['username']

  return render_template("profile.html", name=name,age=age, goal=goal, email=email)


# sets user profile
@app.route("/set_profile", methods=["GET", "POST"])
def set_profile():

  # get records to get previous name and birthday, if already set 
  records = db.child("users").order_by_child("username").equal_to(session['username']).get()
  for record in records.each():
    try:
      name_prev = record.val()['name']
      name = name_prev
    except:
      name_prev = "John Harvard"
      name="not set"
    try: 
      birthday_prev = record.val()['birthday']
    except:
      birthday_prev = "2000-01-01"

  # after form fills
  if request.method == 'POST':

    if request.form.get('name'):
      name = request.form.get('name')
    birthday = request.form.get('birthday')
    goal = float(request.form.get('goal'))

    data = {
      'name': name,
      'birthday': birthday,
      'goal': goal
    }

    # looks for user key and update with provided data
    for user in records.each():
      db.child("users").child(user.key()).update(data)

    return redirect("/profile")

  return render_template("set_profile.html", name_prev=name_prev, birthday_prev=birthday_prev)

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
      session['username'] = username
      data = {
        "username": username
      }
      db.child("users").push(data)
      return redirect("/set_profile")
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

    # add the minutes together first, then hours
    if end_arr[0] == start_arr[0]:
      minutes = end_arr[1] - start_arr[1]
    else:
      minutes = int(end_arr[1]) + (60 - int(start_arr[1]))
      start_arr[0] += 1
    
    hours = int(end_arr[0]) - int(start_arr[0])

    if hours < 0:
      hours += 24
    hours += round(minutes/60, 1)

    username = session["username"]
    track = db.child("sleepTracker").order_by_child("username").equal_to(username).get()
    # empty list is False, empty dict is None
    entered = False
    for day in track.each():
      if day.val()['date'] == date:
        existing_hours = day.val()['hours']
        db.child("sleepTracker").child(day.key()).update({'hours': existing_hours + hours})
        print("tried")
        print(username)
        entered = True
        break 

    if not entered:
      data = {
        'date': date,
        'hours': hours,
        'username': username
      }
      db.child("sleepTracker").push(data)
    
    return redirect("/newnap")

  today = datetime.date.today()
  week_ago = today - datetime.timedelta(days=7)

  return render_template("newnap.html", today=today, week_ago=week_ago)
  
if __name__ == '__main__':
  app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
    