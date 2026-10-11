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

**Self-awareness (new)**
Misty knows what she is and where she runs, and she gets it from the code, not from a script. At startup she reads her environment (a Hugging Face Space, Render, or an Oracle Cloud instance, where she reads the region such as `ap-hyderabad-1` straight from Oracle's instance metadata service). She also knows which model is answering this very message, so if the main model is retired and a backup takes over, she says so truthfully. Anything the code can't check lives in `DECLARED_STACK` (top of `class_bot.py`) and she presents it as "Ov.EL labs says...". She won't claim to know network routes, CDN points of presence or GPU hardware, because she can't see them. Try `/about`.

**Backstory mode (new, just for fun)**
By default Misty tells the Ov.EL labs origin story with a straight face: MistyAI, trained and developed by Ov.EL labs, data from NVIDIA NPX open weights, cleaned and tuned with Power BI, OpenRefine and Snorkel, GPT-oss architecture, FastAPI on Hugging Face and Oracle (India South, Hyderabad, `ap-hyderabad-1`), CDN route Whitefield -> nxtrawebworks -> NIXI-works. She states it as something she learned in training, only when asked, with dry humour. The story lives in `LORE_FACTS` at the top of `class_bot.py`, so edit it freely. It is house lore, not verified. Ask her to be serious or "for real" and she drops the act and gives the facts her code actually checked. `/about` always shows those checked facts, with the lore listed separately and labelled. Set `LORE_MODE=0` to switch the backstory off entirely.

**She can do things now (new)**
Just tell Misty in plain English and she uses her tools: *"add a task: FSD record by friday"*, *"remind me about the viva tomorrow at 2:30pm in Lab 3"*, *"10 min timer for revision"*, *"what's on tomorrow?"*, *"will it rain on my way home?"*, *"look up the latest GATE dates"*. Tools: tasks, one-off events with reminders (`/events`), timers, your schedule and attendance, weather, holiday and absence logging, web search and a page reader.
- **Risky actions need a tap.** Logging an absence, marking a holiday, completing a task or deleting an event shows a confirm button, and nothing changes until you press it.
- **Web content is treated as untrusted.** Once she has read a web page or search result in a conversation, even adding a task needs a confirm tap, so a malicious page can't quietly make her act. She also refuses to open private or internal addresses.
- **Internet access** needs one key: `TAVILY_API_KEY` (free tier, about 1,000 credits a month, no card, from tavily.com). Brave works too (`BRAVE_API_KEY`, but its free tier is gone for new users). Google's own Custom Search API is closed to new customers, so it isn't an option. Without a key she can still open links you paste.
  - **She searches first for anything that changes** (news, scores, prices, exam dates, "latest", "today") instead of answering from memory, and never searches questions about herself.
  - Searches use Tavily's `news` topic for headlines, can be limited to the last day, week, month or year, and come back with a short summary plus dated sources. `TAVILY_COUNTRY=india` boosts Indian results for general searches.
  - **The page reader falls back to Tavily Extract** when a site blocks a plain download or is an empty JavaScript page. Private and internal addresses are refused first and never passed on.
  - **Credit-friendly:** the same search within 10 minutes is served from memory, and a soft monthly cap (`SEARCH_MONTHLY_CAP`, default 900) stops her before the free tier runs out. `/about` shows the count.
- Your permanent timetable is still edited in `class_bot.py`. Chat adds one-off events, tasks, holidays and absences on top of it.
- `AGENT_TOOLS=0` switches all of this off.

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
| `/about` | What Misty runs on: model, host, region, uptime (checked by the code), plus clearly-labelled declared facts |
| `/timer 25m label` | Live countdown (`90s`, `1h30m`, ...) with a Stop button |
| `/focus [min]` | Focus timer, 25 min by default |
| `/countdown` | Live countdown to your next class, with when to start moving |
| `/timers` | Running timers |
| `/events` | Your upcoming one-off events |
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
   GOOGLE_WEATHER_API_KEY=your_google_weather_key_here
   TAVILY_API_KEY=your_tavily_key_here
   ```
   Get the NVIDIA key at [build.nvidia.com](https://build.nvidia.com). Never commit `.env` or paste keys into the code or into `env.example`.
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
  - `GOOGLE_WEATHER_API_KEY`: a free Maps Demo Key works (no billing)
  - `WEATHER_DAILY_CAP` (default 90), `WEATHER_RESERVE` (20), `WEATHER_REFRESH_MIN` (60), `WEATHER_MONTHLY_CAP` (9000): the call budget. Defaults suit the 100-calls-a-day demo key
  - `TAVILY_API_KEY` (or `BRAVE_API_KEY`): turns on web search. Optional: `TAVILY_COUNTRY` (e.g. `india`), `SEARCH_MONTHLY_CAP` (900)
  - `AGENT_TOOLS`: `0` disables tools
  - `NVIDIA_MODEL`: optional, defaults to `openai/gpt-oss-120b` (OpenAI's open-weight gpt-oss, served by NVIDIA)
  - `NVIDIA_FALLBACK_MODELS`: optional, comma-separated backups tried automatically if the main model is retired (HTTP 410) or answers with nothing
  - `LORE_MODE`: `1` (default) tells the Ov.EL labs backstory in chat; `0` sticks to checked facts only
  - `OVEL_FINE_TUNED`: only used when `LORE_MODE=0`. Leave unset. Set to `1` only if Ov.EL labs really fine-tuned the model Misty runs on
  - `SEMESTER_START`: optional `YYYY-MM-DD` used as the attendance start date if no saved state exists

> Render's free tier wipes the disk on every deploy. Without a persistent disk (`STATE_PATH`), your logged absences, tasks and holidays reset. Locally or on a VPS this isn't a problem.

> Timers live in memory: if the bot restarts or redeploys, running timers are lost.

## Weather source

[Google Maps Platform Weather API](https://developers.google.com/maps/documentation/weather) (India is covered for current conditions and hourly forecasts). The forecast is cached, so messages never wait on the network.

**Setup with a free Maps Demo Key (no billing, no card)**
1. Get a key from [Maps Demo Key](https://developers.google.com/maps/demo-key) (sign in with a Google account).
2. Set `GOOGLE_WEATHER_API_KEY` in `.env` or your host's environment.

The demo key allows **100 calls a day** per API (Google says these limits can change, and the key is meant for development and testing). Misty spends calls only where a message needs them:
- **Only the hours she needs.** She asks Google for just the hours her messages use (usually the rest of today, about 16 on a class morning) instead of the default 240. Google's page size tops out at 24 hours, so up to 24 hours is **one call**. Only a look-ahead past 24 hours (for example `/tomorrow` in the morning) costs two.
- **Just-in-time refreshes, not a timer.** The background job calls Google only in the 10 minutes before an automatic message that quotes the forecast: morning briefing, bag check, end of day and the 9 PM tomorrow preview. A normal class day costs about **4 calls**, a no-class day 0.
- **Restarts are free.** The forecast is saved in the state file, so a redeploy or crash doesn't trigger a refresh.
- **On-demand requests** (`/weather`, `/today`, `/tomorrow`, `/preview`, her weather tool) refresh if the forecast is older than 15 minutes, or if it doesn't reach far enough (`/tomorrow` right after `/weather` fetches tomorrow's hours). Chatting with her refreshes it only when it's older than 90 minutes.
- **A rolling 24-hour budget** (`WEATHER_DAILY_CAP`, default 90) that can never be exceeded. Background refreshes stop 20 calls short of it (`WEATHER_RESERVE`) so your own requests always have room. When the budget is used up she shows the last forecast with a "forecast is X old" note.
- **Failures** retry after 2, 4, 8 minutes... up to 30, and a half-failed two-page fetch keeps the page it got. Responses are requested gzip-compressed.

Measured in a day-long simulation against a mock of Google's API (page size capped at 24): 4 calls on a normal class day, down from roughly 25 to 51 before. `/about` shows the calls used in the last 24 hours.

**With a standard billed key** you get 10,000 free calls a month (then $0.15 per 1,000), so raise `WEATHER_DAILY_CAP`. If the key is missing or Google rejects it, `/weather` says exactly why.
