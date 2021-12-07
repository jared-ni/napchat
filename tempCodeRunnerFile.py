
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
        streak 