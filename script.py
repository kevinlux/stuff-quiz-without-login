from requests_html import HTMLSession
import re
from datetime import datetime, timedelta
import pytz
from jinja2 import FileSystemLoader, Environment

def render_from_template(directory, template_name, **kwargs):
    loader = FileSystemLoader(directory)
    env = Environment(loader=loader)
    template = env.get_template(template_name)
    return template.render(**kwargs)


STUFF_ALL_QUIZZES_URL = "https://www.stuff.co.nz/quizzes/"
session = HTMLSession()
r = session.get(STUFF_ALL_QUIZZES_URL)
r.html.render(timeout=30) # almost all page content is rendered by JavaScript, hence render call required
STUFF_ALL_QUIZZES_URL = list(r.html.links) # get all links on page

NZ_TIME = pytz.timezone("Pacific/Auckland") # Ensure timezone is 'Pacific/Auckland)
today = datetime.now(NZ_TIME)
yesterday = today - timedelta(days=1)
date_format = "%B-%d"
# Get today and yesterday date strings in format 'Month-day'
today = today.strftime(date_format)
yesterday = yesterday.strftime(date_format)

quizzes = []

for quiz in STUFF_ALL_QUIZZES_URL:
    # keep only today and yesterday
    if today.lower() in quiz.lower():
        day = today
    elif yesterday.lower() in quiz.lower():
        day = yesterday
    else:
        continue
    
    # add time to date string to make sortable by date
    # morning quiz gets posted at 5am, afternoon quiz at 3pm
    if "morning" in quiz:
        period = "morning"
        day = day + "-05:00"
    elif "afternoon" in quiz:
        period = "afternoon"
        day = day + "-15:00"
    else:
        continue

    quiz_obj = {
        "day": day,
        "period": period,
        "stuffLink": quiz,
    }

    quizzes.append(quiz_obj)

for item in quizzes:
    r = session.get("https://www.stuff.co.nz" + item["stuffLink"])
    r.html.render(timeout=30) # requires js render, same as above
    html = r.html.html
    # extract unique ID from html
    m = re.search('data-rid-id="(.+?)"', html)
    found = m.group(1) 
    # construct Riddle URL
    item["riddleLink"] = "https://www.riddle.com/view/" + found

# sort quizzes from most recent to oldest
quizzes = sorted(
    quizzes,
    key=lambda x: datetime.strptime(x["day"], "%B-%d-%H:%M"),
    reverse=True,
)

with open("./index.html", "w") as fh:
    fh.write(
        render_from_template("./templates", "template.html", quizzes=quizzes)
    )
