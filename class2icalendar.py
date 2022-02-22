from datetime import datetime, timedelta

import requests
from icalendar import Calendar, Event
from pyquery import PyQuery, text

from config import *

DAY = timedelta(days=1)
WEEK = timedelta(days=7)
CLASS_DURATION = timedelta(hours=1, minutes=40)
CLASS_1 = timedelta(hours=8)
CLASS_2 = timedelta(hours=10)
CLASS_3 = timedelta(hours=14)
CLASS_4 = timedelta(hours=16)
CLASS_5 = timedelta(hours=19)
CLASS_DICT = {1: CLASS_1, 2: CLASS_2, 3: CLASS_3, 4: CLASS_4, 5: CLASS_5}


def analyze(str: str, str2: str):
    res = []
    if "," in str:
        res = list(int(i) for i in str.split(","))
    elif "-" in str:
        res = list(range(int(str.split("-")[0]), int(str.split("-")[1]) + 1))
    else:
        res = [int(str)]
    if str2 == "单周":
        res = list(filter(lambda x: x % 2 == 1, res))
    elif str2 == "双周":
        res = list(filter(lambda x: x % 2 == 0, res))
    return res


class_info = []

resp = requests.post(
    "http://csujwc.its.csu.edu.cn/jiaowu/pkgl/llsykb/llsykb_kb.jsp",
    data={
        "type": "xs0101",
        "xnxq01id": semester,
        "xs0101id": id,
        "xs": name,
    },
)
pq = PyQuery(resp.text)
for i, e in enumerate(pq("td[height='28']").items()):
    class_ = {}
    class_["课程"] = e("font[title$=')']").text()
    class_["教师"] = e("font[title='老师']").text()
    class_["周次"] = e("font[title='周次']").text()
    class_["单双周"] = e("font[title='单双周']").text()
    class_["教室"] = e("font[title='上课地点教室']").text()
    if class_["课程"]:
        if " " in class_["课程"]:
            for i, _ in enumerate(class_["课程"].split(" ")):
                cls_ = {}
                cls_["课程"] = class_["课程"].split(" ")[i]
                cls_["教师"] = class_["教师"].split(" ")[i]
                cls_["周次"] = analyze(
                    class_["周次"].split(" ")[i], class_["单双周"].split(" ")[i]
                )

                cls_["周几"] = int(e("font[title$=')']").attr("title")[-6])
                cls_["第几节"] = int(int(e("font[title$=')']").attr("title")[-4]) / 2 + 1)
                cls_["教室"] = class_["教室"].split(" ")[i]
                class_info.append(cls_)
        else:
            class_["周几"] = int(e("font[title$=')']").attr("title")[-6])
            class_["第几节"] = int(int(e("font[title$=')']").attr("title")[-4]) / 2 + 1)
            class_["周次"] = analyze(class_["周次"], class_["单双周"])
            class_info.append(class_)

semester_start = datetime.strptime(semester_start, "%Y-%m-%d")
first_day = semester_start - timedelta(days=semester_start.weekday() + 1) - WEEK

cal = Calendar()
cal.add("x-wr-calname", f"{name}的 {semester} 课表")
cal.add("x-wr-timezone", "Asia/Shanghai")
for class_ in class_info:
    for 周次 in class_["周次"]:
        event = Event()
        event.add("summary", class_["课程"] + "@" + class_["教室"])
        event.add("description", class_["教师"])
        event.add(
            "dtstart",
            first_day + 周次 * WEEK + class_["周几"] % 7 * DAY + CLASS_DICT[class_["第几节"]],
        )
        event.add(
            "dtend",
            first_day
            + 周次 * WEEK
            + class_["周几"] % 7 * DAY
            + CLASS_DICT[class_["第几节"]]
            + CLASS_DURATION,
        )
        cal.add_component(event)

with open(f"{id}.ics", "wb") as f:
    f.write(cal.to_ical())
