# ECG Bot - Ready Project
This project is a ready-to-deploy Telegram bot for teaching ECG (ECG with Abu Eid).
It includes:
- `main.py` : bot code (reads BOT_TOKEN from environment variable `BOT_TOKEN`)
- `requirements.txt` : dependencies
- `cases.json` : 40 example ECG cases (titles, short description, quiz question + options)
- `ecg_cases/` : 40 placeholder PNG images for the cases

## How to deploy
1. Upload this repository to GitHub (or directly zip and deploy to Railway).
2. In Railway (or other host), set environment variable `BOT_TOKEN` to your bot token.
3. Railway will install packages from `requirements.txt` and run `python main.py`.
4. Test the bot in Telegram: send `/start` then use the menu.

## Notes
- The images are placeholders. Replace `ecg_cases/case_<n>.png` with real ECG images as you collect them.
- `cases.json` contains the structure used by `main.py`. You can edit descriptions, quizzes and correct answers.
