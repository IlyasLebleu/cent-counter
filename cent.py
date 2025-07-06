import datetime
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import Counter

def initMediaWikiAPI():
    # We initialize the session
    session = requests.Session()
    session.headers.update({'User-Agent': 'Ilyas Lebleu; [[en:User:Chaotic Enby]]; anti.christ@reborn.com'})
    
    return session

def formatTime(time):
    timeObject = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
    return datetime.datetime.timestamp(timeObject)

def getCentData(session, n, rvstart=""):
    """
    Returns the list of newly created pages
    """

    url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "prop": "revisions",
        "titles": "Template:Centralized discussion",
        "rvlimit": n,
        "rvprop": "timestamp|user|content",
        "rvstart": rvstart,
        "rvslots": "main",
        "formatversion": "2",
        "format": "json"
    }

    R = session.get(url=url, params=params)
    data = R.json()

    pages = data["query"]["pages"][0]["revisions"]

    pages = [{"content":parseWikitext(page["slots"]["main"]["content"]), "timestamp":page["timestamp"], "user":page["user"]} for page in pages if not "texthidden" in page["slots"]["main"]] #convert time to epoch

    return pages

def getMoreCentData(session, n):
    rvstart = ""
    pages = getCentData(session, min(n, 50), rvstart)
    i = n - 50
    while i > 0:
        rvstart = pages[-1]["timestamp"]
        pages.extend(getCentData(session, min(i + 1, 50), rvstart)[1:])
        i -= 49
    for i in range(len(pages)):
        pages[i]["timestamp"] = formatTime(pages[i]["timestamp"])
    return pages

def parseWikitext(content):
    count = 0
    metaCount = 0
    isMeta = False
    for s in content.splitlines():
        if "{{*mp}}" in s:
            count +=1
            continue
        for c in s:
            if c == "*":
                if isMeta:
                    metaCount += 1
                else:
                    count += 1
                break
            if c == "|":
                if "meta" in s:
                    isMeta = True
                    break
            if c != " ":
                break
    return count, metaCount

def plotCentData(data):
    fig, ax = plt.subplots(1, 1)

    rawCent = [[c["content"][i] for c in data] for i in range(2)]
    rawTime = [c["timestamp"] for c in data]
    rawTime.append(datetime.datetime.timestamp(datetime.datetime.now()))

    timeLabels = [datetime.datetime.fromtimestamp(r) for r in rawTime]

    centGraph = ax.stairs(rawCent[0], timeLabels, fill=True, color="#069", label="Local discussions", alpha=0.7)
    centGraph = ax.stairs(rawCent[1], timeLabels, fill=True, color="#5b8", label="Meta discussions", alpha=0.7)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))

    plt.xticks(rotation=45)
    plt.xlabel('Date')
    plt.ylabel('# Discussions')
    plt.title(f'Number of active discussions on WP:CENT')
    plt.legend()

    plt.show()

def getUsers(data):
    users = []
    metaUsers = []

    for i in range(1, len(data)):
        if data[i]["content"][0] > data[i-1]["content"][0]:
            users.append(data[i]["user"])
        if data[i]["content"][1] > data[i-1]["content"][1]:
            metaUsers.append(data[i]["user"])

    return Counter(users).most_common(), Counter(metaUsers).most_common()

centData = getMoreCentData(initMediaWikiAPI(), 500)[::-1]

print(getUsers(centData))
plotCentData(centData)
