import logging
import json
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# =======================
# إعدادات البوت
# =======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

# =======================
# تحميل الحالات من الملف
# =======================
with open("cases.json", "r", encoding="utf-8") as f:
    cases = json.load(f)

# =======================
# لوحة البداية
# =======================
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("📚 التعليم", callback_data="education"),
        InlineKeyboardButton("🩺 الحالات", callback_data="cases"),
        InlineKeyboardButton("📝 الاختبارات", callback_data="tests"),
        InlineKeyboardButton("ℹ️ معلومات", callback_data="info"),
    ]
    keyboard.add(*buttons)
    return keyboard

# =======================
# أوامر البداية
# =======================
@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer("أهلاً يا أبو عيد 🌹\nاختار من القائمة:", reply_markup=main_menu())

# =======================
# التعامل مع القوائم
# =======================
@dp.callback_query_handler(lambda c: c.data == "education")
async def education_section(callback: types.CallbackQuery):
    await callback.message.answer("📚 قسم التعليم:\n- أساسيات ECG\n- كيفية قراءة الموجات\n- الشذوذات الشائعة")

@dp.callback_query_handler(lambda c: c.data == "cases")
async def cases_section(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=3)
    for i, case in enumerate(cases, start=1):
        keyboard.insert(InlineKeyboardButton(f"حالة {i}", callback_data=f"case_{i}"))
    await callback.message.answer("🩺 اختر الحالة:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("case_"))
async def show_case(callback: types.CallbackQuery):
    case_id = int(callback.data.split("_")[1]) - 1
    case = cases[case_id]
    caption = f"📌 {case['title']}\n\n{case['description']}"
    await bot.send_photo(callback.message.chat.id, open(case["image"], "rb"), caption=caption)

@dp.callback_query_handler(lambda c: c.data == "tests")
async def tests_section(callback: types.CallbackQuery):
    await callback.message.answer("📝 قسم الاختبارات:\n- اختبار 1\n- اختبار 2\n(قريبًا الأسئلة التفاعلية)")

@dp.callback_query_handler(lambda c: c.data == "info")
async def info_section(callback: types.CallbackQuery):
    await callback.message.answer("ℹ️ معلومات عن البوت:\nهذا البوت مخصص لتعليم وتدريب ECG.\nالمطور: أبو عيد")

# =======================
# تشغيل البوت
# =======================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
