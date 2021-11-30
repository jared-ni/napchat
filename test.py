import datetime

today = datetime.date.today()
week_ago = today - datetime.timedelta(days=7)

print(week_ago)