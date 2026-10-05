# Misty - Sarcastic College Schedule & Weather Bot

A humorous, CARROT Weather-style Telegram bot that keeps track of college class timetables, alerts you before classes, reminds you to pack your laptop on lab days, and delivers weather forecasts with comedic commentary.

## Features

- ⚡ **Morning Schedule Briefing**: Summarizes your day's lectures at 8:00 AM.
- 🚨 **Class Reminders**: Alerts sent 10 minutes before classes (or immediately when the previous back-to-back class ends).
- 💻 **Laptop / Lab Alerts**: Warns you before leaving home on days with programming or lab classes.
- ☔ **Bangalore Weather Roasts**: Real-time weather reports and rain alerts via `/weather` (Open-Meteo API).
- 🤖 **Interactive Commands**:
  - `/next` – Next upcoming class
  - `/whatstoday` – Full day's schedule
  - `/tomorrow` – Tomorrow's schedule
  - `/weather` – Live weather report and CARROT roast

## Setup & Running Locally

1. **Clone the repository:**
   ```bash
   git clone git@github.com:Rohit-Nadakarni/Misty-.git
   cd Misty-
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   Copy `.env.example` to `.env` and insert your Telegram Bot Token from [@BotFather](https://t.me/BotFather):
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   ```env
   BOT_TOKEN=your_telegram_bot_token_here
   ```

4. **Run the bot:**
   ```bash
   python3 class_bot.py
   ```

5. Open Telegram, search for your bot, and send `/start`.

## Deployment (Render / Cloud)

When deploying to platforms like [Render](https://render.com) as a background/web service:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python3 class_bot.py`
- **Environment Variables**:
  - `BOT_TOKEN`: Your Telegram Bot Token
  - `CHAT_ID`: Your Telegram Chat ID (obtained after sending `/start` to the bot)
  - `PORT`: Automatically set by Render for the keep-alive ping server
