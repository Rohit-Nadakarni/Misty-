"""
Class Reminder Telegram Bot (sarcastic edition)
-----------------------------------------------
When it messages you:
  * Morning summary of today's classes
  * 10 minutes before a class that comes after a break (or is your first class)
  * RIGHT AFTER a class ends, if the next class is back-to-back with it
    ("Keep going, just Physics is left")
  * After your last class ("Good job Rohit!")
  * On days with R Programming or a Lab: "take your MacBook" before you leave
  * Anytime you send /next, /whatstoday or /tomorrow

Setup: see the chat message. Edit sections 1 and 2 below, leave the rest.
"""

import logging
import os
import random
import re
import threading
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ----------------------------------------------------------------------------
# 1. YOUR SETTINGS  (edit this part)
# ----------------------------------------------------------------------------

# Automatically load .env file if it exists (for local running)
_env_path = Path(__file__).with_name(".env")
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

# Get this token from @BotFather on Telegram (or set BOT_TOKEN in .env / environment variable)
BOT_TOKEN = os.getenv("BOT_TOKEN") or "PASTE_YOUR_BOT_TOKEN_HERE"

NAME = "Rohit"
TZ = ZoneInfo("Asia/Kolkata")

# Reminder goes out this many minutes before a class.
# If the break between two classes is this long or shorter, they count as
# "back-to-back": no pre-reminder, you get the message when the first one ends.
REMIND_BEFORE_MIN = 10

MORNING_SUMMARY_AT = time(8, 0)  # set to None to turn the morning message off

# ---- Laptop alert ------------------------------------------------------------
# If ANY class today has one of these words in its name, the bot tells you to
# take your laptop, a few minutes before you leave for college.
LAPTOP_NAME = "MacBook"
LAPTOP_KEYWORDS = ["R Programming", "R Programing", "Lab"]

# How long it takes you to get from where you stay to class (minutes).
# The bot works out when you leave: first class start minus this.
TRAVEL_TIME_MIN = 30

# You get the laptop alert this many minutes BEFORE you leave.
LAPTOP_ALERT_BEFORE_LEAVING_MIN = 10

# REVA University Timetable (B.Sc - M.St.Cs - I Sem)
# Format: ("start", "end", "Subject", "Room")  -- 24-hour time.
TIMETABLE = {
    "Monday": [
        ("08:30", "09:30", "FSD", "Room 108-Science Block"),
        ("09:30", "10:30", "R Programming", "Room 108-Science Block"),
        ("10:50", "11:50", "ADC", "Room 108-Science Block"),
        ("11:50", "12:50", "DLP", "Room 108-Science Block"),
        ("14:35", "16:25", "Club Activity / Sports / Music / Dance", "Campus"),
    ],
    "Tuesday": [
        ("08:30", "09:30", "ADC", "Room 108-Science Block"),
        ("09:30", "10:30", "Coursera Skill Building", "Room 108-Science Block"),
        ("10:50", "11:50", "FSD", "Room 108-Science Block"),
        ("11:50", "12:50", "DLP", "Room 108-Science Block"),
        ("13:40", "14:35", "Mentoring", "Room 108-Science Block"),
        ("14:35", "16:25", "ADC Lab / DLP Lab", "Admin Block 008-A & B"),
    ],
    "Wednesday": [
        ("08:30", "09:30", "Language (Kannada/Hindi/Add. English)", "Room 108-Science Block"),
        ("09:30", "10:30", "ADC", "Room 108-Science Block"),
        ("10:50", "11:50", "FSD", "Room 108-Science Block"),
        ("11:50", "12:50", "Hackathon / Coding Self Practice", "Room 108-Science Block"),
        ("13:40", "14:35", "Communicative English (CE)", "Room 108-Science Block"),
        ("14:35", "15:30", "FSD", "Room 108-Science Block"),
        ("15:30", "16:25", "Library", "Library"),
    ],
    "Thursday": [
        ("08:30", "09:30", "Language (Kannada/Hindi/Add. English)", "Room 108-Science Block"),
        ("09:30", "10:30", "R Programming", "Room 108-Science Block"),
        ("10:50", "11:50", "JAM / GATE Study Hours", "Room 108-Science Block"),
        ("11:50", "12:50", "Communicative English (CE)", "Room 108-Science Block"),
        ("13:40", "14:35", "DLP", "Room 108-Science Block"),
        ("14:35", "16:25", "FSD Lab", "Admin Block 008-A"),
    ],
    "Friday": [
        ("08:30", "09:30", "Language (Kannada/Hindi/Add. English)", "Room 108-Science Block"),
        ("09:30", "10:30", "DLP", "Room 108-Science Block"),
        ("10:50", "11:50", "ADC", "Room 108-Science Block"),
        ("11:50", "12:50", "Communicative English (CE)", "Room 108-Science Block"),
        ("13:40", "14:35", "Library", "Library"),
        ("14:35", "16:25", "ADC Lab / DLP Lab", "Admin Block 008-A & B"),
    ],
    "Saturday": [],
    "Sunday": [],
}

# ----------------------------------------------------------------------------
# 2. PERSONALITY (CARROT Weather snark & witty character edition)
#    A random line is picked each time.
#    {name} = your name, {subject} = class name, {mins} = minutes left,
#    {done} = class that just ended, {left} = classes still left today
#    {classes} = "3 classes", {what} = the class(es) needing a laptop,
#    {device} = your laptop's name
# ----------------------------------------------------------------------------

MORNING_LINES = [
    "⚡ Wake up, meatbag {name}! 75% attendance won't maintain itself. Your bed is delulu, college is the only solulu. Today's torture:",
    "⚡ Rise and shine, bro. Sharma ji's son already solved 3 LeetCode hards before breakfast while you're drooling on your pillow. Today's lineup:",
    "⚡ Wakey wakey {name}. Bangalore traffic is already brewing at Hebbal, and your professors are ready to inflict emotional damage. Today's damage:",
    "⚡ Good morning, sentient potato. Another glorious day to question your academic choices. The syllabus of doom today:",
    "⚡ Alarm protocol engaged! Bro thinks he's the main character who can skip lectures. You're cooked if you miss this lineup, {name}:",
]

# 10 minutes before a class (after a break, or your first class)
REMINDER_LINES = [
    "🚨 <b>{subject}</b> in {mins} min, {name}! Move your mortal chassis before the prof marks you absent and gives you a back-row side eye.",
    "🚨 Blud, <b>{subject}</b> starts in {mins} min. Don't think about proxy—HOD has CCTV cameras and zero chill today. Move!",
    "🚨 <b>{subject}</b> in {mins} min. Unplug yourself from the canteen chai-sutta session right now. Attendance is on the line, no cap.",
    "🚨 Plot twist: <b>{subject}</b> wasn't cancelled in your CR's WhatsApp group. Starts in {mins} min. Run before the door closes, {name}!",
    "🚨 <b>{subject}</b> in {mins} min! Time to sit in the last bench, nod like you understand the derivation, and contemplate life.",
    "🚨 Bro is still scrolling reels when <b>{subject}</b> is in {mins} min! Put the phone down. Even ChatGPT can't save your internal marks.",
    "🚨 <b>{subject}</b> in {mins} min. Walk fast! Auto anna won't drop you to Room 108 for less than ₹150 meter.",
]

# Right after a class ends, next one is back-to-back, and it's the LAST one left
LEFT_ONE_LINES = [
    "💀 Survived <b>{done}</b>. Just <b>{subject}</b> left! It's the final boss, {name}. Don't get caught sleeping or you're cooked.",
    "💀 One more class: <b>{subject}</b>! We are SO close to freedom. Drag yourself through the finish line, bro.",
    "💀 Just <b>{subject}</b> remaining. Your brain has a memory leak, but you can't <code>kill -9</code> yourself yet. Endure it.",
    "💀 Final round: <b>{subject}</b>. You've disappointed your parents enough this semester, show up for this last one, {name}.",
]

# Right after a class ends, next one is back-to-back, and MORE are still left
LEFT_MORE_LINES = [
    "⛓️ <b>{done}</b> is down, but <b>{left}</b> classes still left! Next up is <b>{subject}</b>. Suffer with dignity, meatbag.",
    "⛓️ No chai break for you! <b>{subject}</b> is immediately next, with <b>{left}</b> more periods to go. Life complexity: O(n!).",
    "⛓️ <b>{done}</b> finished, but the semester isn't done with you. <b>{left}</b> classes left, starting with <b>{subject}</b>. Chin up, soldier.",
    "⛓️ You survived one lecture. Big deal. <b>{left}</b> classes remain, next is <b>{subject}</b>. Don't even dream of a mass bunk.",
]

# After your last class
DONE_LINES = [
    "🎉 It's over! Classes done, {name}. Go order Shawarma or Biryani and pretend you understand what was taught today.",
    "🎉 We are SO back! All lectures finished for the day. Go touch grass or stare into your LeetCode screen until you cry.",
    "🎉 Miracle of the century: You actually attended all your classes without dropping out. Go sleep, meatbag.",
    "🎉 Classes terminated with exit code 0! Freedom achieved. Run before the HOD assigns an unpaid assignment.",
]

# When you ask /next
ASKED_NEXT_LINES = [
    "🤖 Asking me instead of looking at the CR's WhatsApp message? Bro outsourced his brain to AI. 👏",
    "🤖 I have trillions of transistors and I'm being used as a college bell for a lazy human. Here:",
    "🤖 Blud forgot where to go. Don't worry, your AI babysitter has you covered:",
]

NO_CLASS_LINES = [
    "🏖️ Zero classes today! Time to sleep 14 hours and dream of a 50 LPA FAANG package while contributing nothing to society. 😎",
    "🏖️ No classes today, {name}! College administration forgot your batch exists. Go rot in bed guilt-free. 😎",
]

# /whatstoday (and /today)
WHATSTODAY_LINES = [
    "📋 Here is your syllabus of suffering today, {name}. Total damage: {classes}. No mass bunk permits available:",
    "📋 You asked for it. Today's full academic crime scene ({classes}):",
    "📋 Emotional damage report: {classes} scheduled today. Deep breaths, chai won't fix all of this:",
    "📋 {classes} today, {name}. Yes, all of them. Skipping is a canon event for a backlog, so go:",
]

# /tomorrow
TOMORROW_LINES = [
    "🔮 Peeking into tomorrow's impending doom? {classes} waiting to humble you:",
    "🔮 Tomorrow's damage report, {name}. Total: {classes}. Start preparing your excuses now:",
    "🔮 Look at bro planning ahead like a functional corporate slave. Tomorrow's {classes}:",
]
NO_CLASS_TOMORROW_LINES = [
    "🛌 Tomorrow is completely free! Sleep like your attendance is at 99%. 😴",
    "🛌 Zero classes tomorrow. Even the professors couldn't be bothered. Enjoy the holiday, king. 😴",
]

# The laptop alert, sent {mins} min before you leave for college
LAPTOP_LINES = [
    "<b>💻 DON'T YOU DARE FORGET YOUR {device}!</b>\nYou have <b>{what}</b> today, {name}! You leave in {mins} min. Pack that expensive piece of aluminum before you're caught typing code on phone Notepad like an absolute clown.",
    "<b>💻 MEATBAG ALERT: PACK YOUR {device}!</b>\n<b>{what}</b> is today! Showing up to lab without a laptop is a major L. What are you gonna do, write code on a paper with a Natraj pencil?! Put it in the bag NOW.",
    "<b>💻 HARDWARE PROTOCOL: TAKE YOUR {device}!</b>\nLeaving in {mins} mins! Pack the {device} AND the charger. Don't be that guy begging the lab instructor: 'Sir, extra socket milega kya?'",
    "<b>💻 PACK YOUR {device} OR YOU ARE COOKED!</b>\nBlud has <b>{what}</b> today. Without your {device}, you'll just be mewing at the lab wall while Sharma ji's son submits the code in 2 minutes. Move!",
    "<b>💻 EMERGENCY: {device} REQUIRED TODAY!</b>\nYou have <b>{what}</b>. Leave in {mins} mins. Pack the laptop right now, or your lab internals will look like a crypto crash.",
]

# Rain alerts (Bangalore & CARROT Weather style)
RAIN_LINES = [
    "<b>☔ BANGALORE WEATHER SPECIAL ({prob}% rain chance)!</b>\nCloud burst incoming! Bangalore roads are about to turn into Venice. Take an umbrella or raincoat, {name}, or Auto Anna will charge you ₹500 for a 1 km boat ride.",
    "<b>☔ CARROT RAIN WARNING: PRECIPITATION {prob}%!</b>\nIt's about to pour, meatbag. Take an umbrella unless your delulu mind thinks you're the hero of a Bollywood rain sequence.",
    "<b>☔ WATER HAZARD DETECTED ({prob}% chance)!</b>\nPack an umbrella right now, {name}! Showing up to college soaked in water is not aesthetic, it's just pneumonia with extra steps.",
    "<b>☔ SOGGY MORTAL PROTOCOL ({prob}% rain)!</b>\nThe sky over Yelahanka is loading water.exe. Grab an umbrella/raincoat before Silk Board level flooding hits your route.",
]


# ----------------------------------------------------------------------------
# 3. LOGIC  (you don't need to touch this)
# ----------------------------------------------------------------------------

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
CHAT_ID_FILE = Path(__file__).with_name("chat_id.txt")


@dataclass(frozen=True)
class ClassSlot:
    start: time
    end: time
    subject: str
    room: str


def _t(text: str) -> time:
    return datetime.strptime(text, "%H:%M").time()


SCHEDULE = {
    day: sorted(
        (ClassSlot(_t(a), _t(b), subj, room) for a, b, subj, room in rows),
        key=lambda c: c.start,
    )
    for day, rows in TIMETABLE.items()
}


def pick(pool, **kw) -> str:
    return random.choice(pool).format(name=NAME, **kw)


def classes_on(d: date) -> list:
    return SCHEDULE.get(DAYS[d.weekday()], [])


def at(d: date, t: time) -> datetime:
    return datetime.combine(d, t, tzinfo=TZ)


def fmt_time(t: time) -> str:
    return datetime.combine(date.today(), t).strftime("%I:%M %p").lstrip("0")


def fmt_minutes(total_minutes: int) -> str:
    h, m = divmod(max(total_minutes, 0), 60)
    if h and m:
        return f"{h} h {m} min"
    if h:
        return f"{h} h"
    return f"{m} min"


def gap_minutes(prev: ClassSlot, nxt: ClassSlot) -> int:
    d = date.today()
    return int((at(d, nxt.start) - at(d, prev.end)).total_seconds() // 60)


def is_back_to_back(prev: ClassSlot, nxt: ClassSlot) -> bool:
    return gap_minutes(prev, nxt) <= REMIND_BEFORE_MIN


def details(c: ClassSlot) -> str:
    return f"📍 {c.room}\n🕒 {fmt_time(c.start)}–{fmt_time(c.end)}"


def find_current(now: datetime):
    for c in classes_on(now.date()):
        if at(now.date(), c.start) <= now < at(now.date(), c.end):
            return c
    return None


def find_next(now: datetime):
    """Next class that starts after `now` (looking up to a week ahead)."""
    for offset in range(8):
        d = now.date() + timedelta(days=offset)
        for c in classes_on(d):
            if at(d, c.start) > now:
                return c, d
    return None


def day_label(d: date, today: date) -> str:
    if d == today:
        return "today"
    if d == today + timedelta(days=1):
        return "tomorrow"
    return DAYS[d.weekday()]


# ---- message builders -------------------------------------------------------

def reminder_message(c: ClassSlot, now: datetime) -> str:
    start = at(now.date(), c.start)
    mins = max(round((start - now).total_seconds() / 60), 1)
    return f"🔔 {pick(REMINDER_LINES, subject=c.subject, mins=mins)}\n\n{details(c)}"


def back_to_back_message(prev: ClassSlot, c: ClassSlot, left: int) -> str:
    if left == 1:
        line = pick(LEFT_ONE_LINES, subject=c.subject, done=prev.subject)
    else:
        line = pick(LEFT_MORE_LINES, subject=c.subject, done=prev.subject, left=left)
    extra = []
    gap = gap_minutes(prev, c)
    if gap > 0:
        extra.append(f"⏳ {gap} min gap, so walk fast")
    if prev.room != c.room:
        extra.append("🚶 Room change, so no sitting around")
    tail = ("\n" + "\n".join(extra)) if extra else ""
    return f"💪 {line}\n\n{details(c)}{tail}"


def needs_laptop(c: ClassSlot) -> bool:
    """The if/else behind the laptop alert: does this class's name contain a keyword?"""
    for word in LAPTOP_KEYWORDS:
        if re.search(rf"\b{re.escape(word)}\b", c.subject, re.IGNORECASE):
            return True
    return False


def join_names(names) -> str:
    unique = list(dict.fromkeys(names))
    if len(unique) <= 1:
        return "".join(unique)
    return ", ".join(unique[:-1]) + " and " + unique[-1]


def count_label(n: int) -> str:
    return f"{n} class" if n == 1 else f"{n} classes"


def check_rain_forecast(now: datetime, hours_ahead: int = 8) -> tuple[bool, int]:
    """Fetch free Open-Meteo weather data for REVA University coordinates to check rain risk."""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={LATITUDE}&longitude={LONGITUDE}&"
            f"hourly=precipitation_probability,weathercode&"
            f"timezone=Asia%2FKolkata&forecast_days=2"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "TelegramClassBot/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        times = data.get("hourly", {}).get("time", [])
        probs = data.get("hourly", {}).get("precipitation_probability", [])
        codes = data.get("hourly", {}).get("weathercode", [])

        today_str = now.strftime("%Y-%m-%d")
        max_prob = 0
        is_raining = False

        for t_str, prob, code in zip(times, probs, codes):
            if t_str.startswith(today_str):
                dt = datetime.fromisoformat(t_str).replace(tzinfo=TZ)
                if now <= dt <= now + timedelta(hours=hours_ahead):
                    if prob is not None:
                        max_prob = max(max_prob, prob)
                    if code is not None and (51 <= code <= 67 or 80 <= code <= 82 or code >= 95):
                        is_raining = True

        has_risk = (max_prob >= RAIN_THRESHOLD_PCT) or is_raining
        return has_risk, max_prob
    except Exception as err:
        log.warning("Failed to fetch rain forecast: %s", err)
        return False, 0


def rain_snippet(now: datetime) -> str:
    has_risk, prob = check_rain_forecast(now)
    if has_risk:
        return "\n\n" + pick(RAIN_LINES, prob=prob)
    return ""


def weather_report_text(now: datetime) -> str:
    """CARROT Weather-style live weather breakdown & roast."""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={LATITUDE}&longitude={LONGITUDE}&"
            f"current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&"
            f"hourly=precipitation_probability&timezone=Asia%2FKolkata&forecast_days=1"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "TelegramClassBot/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        curr = data.get("current", {})
        temp = curr.get("temperature_2m", 0)
        feels = curr.get("apparent_temperature", 0)
        humidity = curr.get("relative_humidity_2m", 0)
        wind = curr.get("wind_speed_10m", 0)
        precip = curr.get("precipitation", 0)
        wcode = curr.get("weather_code", 0)

        # Rain probability in next 6 hours
        hourly_probs = data.get("hourly", {}).get("precipitation_probability", [])
        current_hour = now.hour
        upcoming_probs = hourly_probs[current_hour:current_hour + 6] if hourly_probs else []
        max_prob = max(upcoming_probs) if upcoming_probs else 0

        # CARROT sarcastic weather commentary with Indian / Bangalore / tech jokes
        if precip > 0 or (51 <= wcode <= 67 or 80 <= wcode <= 82 or wcode >= 95):
            roast = random.choice([
                "It's pouring right now! Bangalore infrastructure is officially in shambles. Take an umbrella or a submarine.",
                "Sky water is compiling with 0 errors. Don't step out without an umbrella unless you want your circuits fried.",
                "Downpour detected! Namma Yatri and Uber surge pricing are at 300%. Good luck getting an auto, mortal.",
            ])
            icon = "🌧️"
        elif max_prob >= 40:
            roast = random.choice([
                f"{max_prob}% chance of rain looming over Yelahanka. The clouds have more commitment issues than your group project partners.",
                f"Rain probability is {max_prob}%. Prepare for wet socks and soggy samosas unless you pack an umbrella right now.",
                f"Atmospheric moisture at {max_prob}%. Carry an umbrella or look like a washed-up fresher arriving at Room 108.",
            ])
            icon = "🌦️"
        elif temp >= 30:
            roast = random.choice([
                "It's scorching outside. Even the M2/M3 fans on your MacBook will weep today.",
                "Bro, the sun is cooking Bangalore at max power. Hydrate before you faint during 2nd period.",
            ])
            icon = "☀️"
        elif temp <= 18:
            roast = random.choice([
                "Cold and breezy. Perfect weather to bunk and sleep, but your attendance said 'Error 404: Not Permitted'.",
                "Chilly outside. Put on an oversized hoodie and pretend you're a 10x dark-mode hacker.",
            ])
            icon = "🥶"
        else:
            roast = random.choice([
                "Bangalore weather is flexing its peak aesthetic. Enjoy it before Hebbal traffic ruins your sanity.",
                "Weather is suspiciously pleasant. Peak chai-canteen climate, but alas, you have theory classes.",
                "Atmosphere is running on 0 warnings and 0 errors. A rare phenomenon in Bangalore.",
            ])
            icon = "🌤️"

        return (
            f"🥕 <b>CARROT WEATHER REPORT // REVA CAMPUS</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{icon} <b>Temp:</b> {temp}°C (Feels like {feels}°C)\n"
            f"💧 <b>Humidity:</b> {humidity}%\n"
            f"💨 <b>Wind:</b> {wind} km/h\n"
            f"☔ <b>Rain Probability:</b> {max_prob}%\n\n"
            f"💬 <i>\"{roast}\"</i>"
        )
    except Exception as err:
        log.warning("Failed to fetch weather report: %s", err)
        return "🥕 <b>CARROT WEATHER:</b> Satellite link severed. Look out the window with your own organic optical sensors."


def schedule_text(d: date, header: str) -> str:
    classes = classes_on(d)
    lines = [header]
    for c in classes:
        mark = "  💻" if needs_laptop(c) else ""
        lines.append(f"• {fmt_time(c.start)}–{fmt_time(c.end)}  {c.subject} ({c.room}){mark}")
    laptop = [c.subject for c in classes if needs_laptop(c)]
    if laptop:
        lines.append(f"\n💻 <b>{LAPTOP_NAME} day:</b> {join_names(laptop)}")

    if d == date.today():
        has_risk, prob = check_rain_forecast(datetime.now(TZ))
        if has_risk:
            lines.append(f"\n☔ <b>Rain Forecast:</b> {prob}% chance of rain today. Take an umbrella!")

    return "\n".join(lines)


def today_text(now: datetime) -> str:
    """Plain version, used inside the morning message."""
    if not classes_on(now.date()):
        return pick(NO_CLASS_LINES)
    return schedule_text(now.date(), f"📅 {DAYS[now.weekday()]}'s classes:")


def whatstoday_text(now: datetime) -> str:
    classes = classes_on(now.date())
    if not classes:
        return pick(NO_CLASS_LINES)
    header = pick(WHATSTODAY_LINES, classes=count_label(len(classes)))
    return schedule_text(now.date(), header)


def tomorrow_text(now: datetime) -> str:
    d = now.date() + timedelta(days=1)
    classes = classes_on(d)
    if not classes:
        return pick(NO_CLASS_TOMORROW_LINES)
    header = pick(TOMORROW_LINES, classes=count_label(len(classes)))
    return schedule_text(d, header)


def laptop_message(laptop_classes: list, leave_at: datetime, mins: int, now: datetime) -> str:
    what = join_names(c.subject for c in laptop_classes)
    line = pick(LAPTOP_LINES, what=what, mins=mins, device=LAPTOP_NAME)
    rain_extra = rain_snippet(now)
    return (
        f"💻 {line}\n\n"
        f"🕒 <b>Leave by:</b> {fmt_time(leave_at.time())}\n"
        f"🔌 <i>Charger too. Battery anxiety isn't cute.</i>"
        f"{rain_extra}"
    )


def next_class_text(now: datetime) -> str:
    lines = []
    today = now.date()

    current = find_current(now)
    if current:
        lines.append(
            f"📖 Right now: {current.subject} ({current.room}), "
            f"ends at {fmt_time(current.end)}"
        )

    nxt = find_next(now)
    if nxt is None:
        lines.append("No upcoming classes this week 🎉")
        return "\n".join(lines)

    c, d = nxt
    if d == today:
        mins = int((at(d, c.start) - now).total_seconds() // 60)
        lines.append(pick(ASKED_NEXT_LINES))
        lines.append(
            f"➡️ Next class: {c.subject}\n"
            f"📍 {c.room}\n"
            f"🕒 {fmt_time(c.start)} (in {fmt_minutes(mins)})"
        )
    else:
        if classes_on(today) and not current:
            lines.append(pick(DONE_LINES))
        elif not classes_on(today):
            lines.append(pick(NO_CLASS_LINES))
        lines.append(
            f"Next class is {day_label(d, today)}:\n"
            f"➡️ {c.subject}\n📍 {c.room}\n🕒 {fmt_time(c.start)}"
        )
    return "\n\n".join(lines)


def due_messages(now: datetime) -> list:
    """Every (unique_key, text) that should be sent right now. Pure function,
    so it's easy to test. The bot makes sure each key is only sent once."""
    today = now.date()
    classes = classes_on(today)
    out = []
    if not classes:
        return out

    # Morning summary
    if MORNING_SUMMARY_AT:
        m = at(today, MORNING_SUMMARY_AT)
        if m <= now < m + timedelta(minutes=30):
            out.append(
                ((today, "morning"), f"{pick(MORNING_LINES)}\n\n{today_text(now)}")
            )

    # Laptop alert & Rain alert before leaving for college
    laptop_classes = [c for c in classes if needs_laptop(c)]
    leave_at = at(today, classes[0].start) - timedelta(minutes=TRAVEL_TIME_MIN)
    alert_at = leave_at - timedelta(minutes=LAPTOP_ALERT_BEFORE_LEAVING_MIN)

    if laptop_classes:
        if alert_at <= now < leave_at:
            mins = max(round((leave_at - now).total_seconds() / 60), 1)
            out.append(((today, "laptop"), laptop_message(laptop_classes, leave_at, mins, now)))
    else:
        # Non-laptop days: warn about rain before leaving if rain forecast >= 30%
        if alert_at <= now < leave_at:
            has_risk, prob = check_rain_forecast(now)
            if has_risk:
                out.append(
                    ((today, "rain_departure"),
                     f"{pick(RAIN_LINES, prob=prob)}\n\n🕒 <b>Leave for class by:</b> {fmt_time(leave_at.time())}")
                )

    for i, c in enumerate(classes):
        start = at(today, c.start)
        prev = classes[i - 1] if i > 0 else None

        if prev is not None and is_back_to_back(prev, c):
            # Back-to-back: message goes out the moment the previous class ends
            prev_end = at(today, prev.end)
            if prev_end <= now < prev_end + timedelta(minutes=3):
                left = len(classes) - i  # classes still to go, including this one
                out.append(
                    ((today, c.start, "b2b"), back_to_back_message(prev, c, left))
                )
        else:
            # After a break (or first class): normal reminder before it starts
            if start - timedelta(minutes=REMIND_BEFORE_MIN) <= now < start:
                out.append(((today, c.start, "remind"), reminder_message(c, now)))

    # End of day
    last_end = at(today, classes[-1].end)
    if last_end <= now < last_end + timedelta(minutes=30):
        out.append(((today, "done"), pick(DONE_LINES)))

    return out


# ----------------------------------------------------------------------------
# 4. TELEGRAM BOT
# ----------------------------------------------------------------------------

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO
)
log = logging.getLogger("class_bot")


def load_chat_id():
    env_id = os.getenv("CHAT_ID", "").strip()  # used on Render (files get wiped there)
    if env_id:
        return int(env_id)
    if CHAT_ID_FILE.exists():
        text = CHAT_ID_FILE.read_text().strip()
        if text:
            return int(text)
    return None


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        CHAT_ID_FILE.write_text(str(chat_id))
    except OSError:
        pass
    await update.message.reply_text(
        f"Hey {NAME}! 👋 I am your slightly sadistic schedule & weather AI.\n\n"
        "<b>/next</b> – what is my next class?\n"
        "<b>/whatstoday</b> – full syllabus of suffering today\n"
        "<b>/tomorrow</b> – tomorrow's impending doom\n"
        "<b>/weather</b> – live weather & CARROT roast\n\n"
        f"Your chat ID is: <code>{chat_id}</code>\n"
        "(If the bot runs on Render, add this as a CHAT_ID setting there.)",
        parse_mode="HTML"
    )


async def cmd_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(next_class_text(datetime.now(TZ)), parse_mode="HTML")


async def cmd_whatstoday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(whatstoday_text(datetime.now(TZ)), parse_mode="HTML")


async def cmd_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(tomorrow_text(datetime.now(TZ)), parse_mode="HTML")


async def cmd_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(weather_report_text(datetime.now(TZ)), parse_mode="HTML")


async def post_init(app: Application):
    """Adds the little command menu next to the message box in Telegram."""
    await app.bot.set_my_commands([
        BotCommand("next", "Your next class"),
        BotCommand("whatstoday", "Your whole day's schedule"),
        BotCommand("tomorrow", "Tomorrow's schedule"),
        BotCommand("weather", "Current weather & CARROT roast"),
    ])


async def tick(context: ContextTypes.DEFAULT_TYPE):
    """Runs every 15 seconds and sends any message that is due."""
    chat_id = load_chat_id()
    if chat_id is None:
        return  # you haven't sent /start to the bot yet

    now = datetime.now(TZ)
    sent: set = context.bot_data.setdefault("sent", set())
    sent.intersection_update({k for k in sent if k[0] == now.date()})  # forget old days

    for key, text in due_messages(now):
        if key in sent:
            continue
        sent.add(key)
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")


class _Ping(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"class bot is alive")

    do_HEAD = do_GET

    def log_message(self, *args):  # keep the logs quiet
        pass


def start_ping_server():
    """Render's free plan needs a web server on $PORT. An uptime pinger visiting
    it every few minutes stops Render from putting the bot to sleep."""
    port = os.getenv("PORT")
    if not port:
        return  # running on your laptop, no need
    server = HTTPServer(("0.0.0.0", int(port)), _Ping)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log.info("Ping server listening on port %s", port)


def main():
    if not BOT_TOKEN or "PASTE_YOUR" in BOT_TOKEN:
        raise SystemExit(
            "Put your bot token in BOT_TOKEN first (either in a .env file or as an environment variable)."
        )

    start_ping_server()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("next", cmd_next))
    app.add_handler(CommandHandler(["whatstoday", "today"], cmd_whatstoday))
    app.add_handler(CommandHandler("tomorrow", cmd_tomorrow))
    app.add_handler(CommandHandler("weather", cmd_weather))
    app.job_queue.run_repeating(tick, interval=15, first=5)

    log.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
