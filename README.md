# Misty - Dry-Witted College Schedule & Weather Bot

A Telegram bot that knows your real timetable (rooms, free periods, the walk to the library), nudges you at the right moments, reasons about your day, and says it with a straight face.

## What it does

**Automatic messages**
- ☀️ **Morning briefing**: goes out 60 min before you leave home (not at a fixed hour). Lineup, free windows, laptop, umbrella, attendance risks and tasks due.
- 🎒 **Bag check**: 10 min before you leave. One message with `MacBook + charger` and/or `umbrella`, only when needed.
- 🔔 **Class reminders**: 10 min before a class after a break (16 min for classes outside Science Block, because of the walk).
- 💪 **Back-to-back alerts**: sent the moment a class ends. It does the maths: *"Browsing Centre is ~6 min away and the gap is 0, you'll arrive about 6 min late unless you start walking this second."*
- 🎉 **Done for the day**: after your last real class, with rain on the way home, optional free periods still ahead, and tap-to-log absence buttons.
- 🌙 **Evening preview** (9 PM): tomorrow's plan, alarm suggestion, "charge the MacBook tonight".

**Free periods are not classes**
Coursera, Hackathon / Coding Self Practice, Club Activity, JAM / GATE Study Hours and Library are free periods. They never trigger reminders, never count for attendance, and never decide when you leave or when you're done. They show up as **free windows** with a tip instead.

**Weather mapped to your day**
Rain is checked against three legs of your day (on the way in, on campus, on the way home), so "dry at 8 AM, 70% at 4 PM" still gets you an umbrella warning.

**Attendance guardian**
Misty counts classes held from your timetable. You only log what you missed (tap buttons after the last class, or `/bunked`). It shows % per subject, spare bunks, and how many classes in a row you need to climb back above 75%.

**Open-ended chat (new)**
Just type to Misty, or use `/ask`. She answers anything (coursework, trivia, advice) in a deadpan, dry-witted voice, and she knows your live schedule, weather, tasks and attendance, so "can I bunk the 2:35?" gets a real answer. The personality is baked into `PERSONA_PROMPT` in `class_bot.py`. Powered by NVIDIA NIM (OpenAI-compatible API).

**Live timers and previews (new)**
Timers tick inside the chat: one message that edits itself with a progress bar and a Stop button, then pings you when done. Say "timer 10 min" in plain English or use the commands below. `/preview` shows any automatic message (morning, bag check, tomorrow, end of day) on demand.

## Commands

| Command | What it does |
|---|---|
| `/next` | Next class, when to leave or start walking |
| `/whatstoday` (`/today`) | Today in full |
| `/tomorrow` | Tomorrow in full |
| `/free` | Free windows left today |
| `/weather` | Weather and rain mapped to your schedule |
| `/attendance` | % per subject, spare bunks, recovery plan |
| `/bunked [date]` | Log missed classes (`/bunked`, `/bunked yesterday`, `/bunked friday`, `/bunked 2026-10-09`) |
| `/holiday [date]` | Toggle a no-class day: no reminders, no attendance impact |
| `/task text by friday` | Add a deadline (`today`, `tomorrow`, a weekday, `14/10`, `2026-10-14`) |
| `/tasks`, `/done n` | List and tick off tasks |
| `/setstart YYYY-MM-DD` | Date attendance counting begins |
| *(just type)* or `/ask text` | Ask Misty anything, answered in character |
| `/reset` | Clear Misty's chat memory |
| `/timer 25m label` | Live countdown (`90s`, `1h30m`, ...) with a Stop button |
| `/focus [min]` | Focus timer, 25 min by default |
| `/countdown` | Live countdown to your next class, with when to start moving |
| `/timers` | Running timers |
| `/preview [morning\|bag\|evening\|done]` | See an automatic message on demand |

## Settings worth knowing (top of `class_bot.py`)

- `FREE_PERIOD_KEYWORDS`: anything with these words in its name is a free period. Add `"Mentoring"` if you want it treated as free.
- `WALK_BETWEEN_BUILDINGS_MIN`: my estimate (6 min) for Science Block <-> Library / Admin Block. Time the walk once and tweak it.
- `TRAVEL_TIME_MIN`, `BRIEFING_BEFORE_LEAVING_MIN`, `EVENING_PREVIEW_AT`, `MIN_ATTENDANCE_PCT`.
- Room 201 (Friday Additional English) is assumed to be in Science Block, 2nd floor.

## Setup & running locally

1. **Clone the repository:**
   ```bash
   git clone git@github.com:Rohit-Nadakarni/Misty-.git
   cd Misty-
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment variables:** copy `.env.example` to `.env` and add your token from [@BotFather](https://t.me/BotFather):
   ```env
   BOT_TOKEN=your_telegram_bot_token_here
   NVIDIA_API_KEY=your_nvidia_nim_key_here
   ```
   Get the NVIDIA key at [build.nvidia.com](https://build.nvidia.com). Never commit `.env` or paste keys into the code.
4. **Run the bot:**
   ```bash
   python3 class_bot.py
   ```
5. Open Telegram, find your bot, send `/start`. The first chat to send `/start` becomes the owner; everyone else is turned away.
6. Send `/setstart YYYY-MM-DD` with your real semester start date, then log anything you've missed since with `/bunked <date>`.

## Deployment (Render / Cloud)

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python3 class_bot.py`
- **Environment Variables**:
  - `BOT_TOKEN`: your Telegram bot token
  - `CHAT_ID`: your chat ID (shown after `/start`)
  - `PORT`: set automatically by Render for the keep-alive ping server
  - `STATE_PATH`: where absences, tasks and holidays are saved, e.g. `/data/bot_state.json` on a Render persistent disk
  - `NVIDIA_API_KEY`: key for the AI chat (without it, chat is off but everything else works)
  - `NVIDIA_MODEL`: optional, defaults to `meta/llama-3.3-70b-instruct`
  - `SEMESTER_START`: optional `YYYY-MM-DD` used as the attendance start date if no saved state exists

> Render's free tier wipes the disk on every deploy. Without a persistent disk (`STATE_PATH`), your logged absences, tasks and holidays reset. Locally or on a VPS this isn't a problem.

> Timers live in memory: if the bot restarts or redeploys, running timers are lost.

## Weather source

[Open-Meteo](https://open-meteo.com) (free, no key). The forecast is fetched in the background every ~20 minutes and cached, so messages never wait on the network.
