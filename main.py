# main.py
import os
import json
import logging
import random
from pathlib import Path

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN not found in environment. Set BOT_TOKEN variable.")
    raise SystemExit("BOT_TOKEN not set")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

BASE_DIR = Path(__file__).parent

# load cases
cases_path = BASE_DIR / "cases.json"
if not cases_path.exists():
    logger.error("cases.json not found. Make sure it's next to main.py")
    raise SystemExit("cases.json missing")

with open(cases_path, "r", encoding="utf-8") as f:
    CASES = json.load(f)

# Helper: create main menu keyboard
def main_menu_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📚 قسم التعليم", callback_data="menu_teach"),
        InlineKeyboardButton("🩺 حالات ECG", callback_data="menu_cases"),
        InlineKeyboardButton("📝 اختبارات", callback_data="menu_quiz"),
    )
    return kb

@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    text = "أهلًا بك في *ECG with Abu Eid* 👋\nاختر من القائمة أدناه:"
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="Markdown")

# route callback queries
@dp.callback_query_handler(lambda c: True)
async def callbacks_router(callback_query: types.CallbackQuery):
    data = callback_query.data or ""
    # main menu items
    if data == "menu_teach":
        await send_teach_intro(callback_query)
    elif data == "menu_cases":
        await send_cases_list(callback_query, page=0)
    elif data.startswith("cases_page_"):
        page = int(data.split("_")[-1])
        await send_cases_list(callback_query, page=page)
    elif data.startswith("case_") and data.count("_") == 1:
        case_id = int(data.split("_")[-1])
        await send_case_detail(callback_query, case_id)
    elif data == "menu_quiz":
        await send_quiz_menu(callback_query)
    elif data == "quiz_random":
        case = random.choice(CASES)
        await send_quiz_for_case(callback_query, case["id"])
    elif data == "quiz_by_number":
        # ask user to send a number
        await bot.send_message(callback_query.from_user.id, "ارسِل رقم الحالة اللي تبغى تختبرها (مثال: 5)")
        try:
            await callback_query.message.delete()
        except:
            pass
    elif data.startswith("quiz_case_"):
        case_id = int(data.split("_")[-1])
        await send_quiz_for_case(callback_query, case_id)
    elif data.startswith("answer_"):
        # format answer_{caseid}_{index}
        parts = data.split("_")
        if len(parts) == 3:
            case_id = int(parts[1]); idx = int(parts[2])
            await handle_answer(callback_query, case_id, idx)
    elif data == "back_main":
        await back_main(callback_query)
    else:
        await callback_query.answer()  # generic ack

async def send_teach_intro(query):
    text = ("*قسم التعلم*\n\n"
            "مقدمة عن ECG وأساسية القراءة:\n"
            "1. موجة P: atrial depolarization.\n"
            "2. QRS: ventricular depolarization.\n"
            "3. T: ventricular repolarization.\n\n"
            "تقدر ترجع للقائمة بالأسفل.")
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ رجوع للقائمة", callback_data="back_main"))
    # edit or send
    try:
        await query.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except:
        await bot.send_message(query.from_user.id, text, reply_markup=kb, parse_mode="Markdown")
    await query.answer()

async def send_cases_list(query, page=0, per_page=8):
    start = page * per_page
    items = CASES[start:start+per_page]
    kb = InlineKeyboardMarkup(row_width=1)
    for c in items:
        kb.add(InlineKeyboardButton(f"{c['id']}. {c['title']}", callback_data=f"case_{c['id']}"))
    nav = []
    if start > 0:
        nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"cases_page_{page-1}"))
    if start + per_page < len(CASES):
        nav.append(InlineKeyboardButton("التالي ➡️", callback_data=f"cases_page_{page+1}"))
    nav.append(InlineKeyboardButton("⬅️ رجوع للقائمة", callback_data="back_main"))
    kb.row(*nav)
    try:
        await query.message.edit_text("اختر الحالة من القائمة:", reply_markup=kb)
    except:
        await bot.send_message(query.from_user.id, "اختر الحالة من القائمة:", reply_markup=kb)
    await query.answer()

async def send_case_detail(query, case_id):
    case = next((c for c in CASES if c["id"] == case_id), None)
    if not case:
        await query.answer("الحالة غير موجودة", show_alert=True)
        return
    caption = f"*{case['title']}*\n\n{case.get('short_description','')}"
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("📝 اختبار لهذه الحالة", callback_data=f"quiz_case_{case_id}"))
    kb.add(InlineKeyboardButton("⬅️ رجوع للقائمة", callback_data="menu_cases"))
    image_path = BASE_DIR / case["image"]
    try:
        # send photo as a new message (edit text can't include a photo)
        await bot.send_photo(chat_id=query.from_user.id, photo=open(image_path, "rb"), caption=caption, parse_mode="Markdown", reply_markup=kb)
        try:
            await query.message.delete()
        except:
            pass
    except Exception as e:
        logger.exception("Failed to send image: %s", e)
        # fallback: send text only
        try:
            await query.message.edit_text(caption, reply_markup=kb, parse_mode="Markdown")
        except:
            await bot.send_message(query.from_user.id, caption, reply_markup=kb, parse_mode="Markdown")
    await query.answer()

async def send_quiz_menu(query):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("اختبار عشوائي", callback_data="quiz_random"))
    kb.add(InlineKeyboardButton("اختبار حسب رقم الحالة", callback_data="quiz_by_number"))
    kb.add(InlineKeyboardButton("⬅️ رجوع للقائمة", callback_data="back_main"))
    try:
        await query.message.edit_text("اختر نوع الاختبار:", reply_markup=kb)
    except:
        await bot.send_message(query.from_user.id, "اختر نوع الاختبار:", reply_markup=kb)
    await query.answer()

async def send_quiz_for_case(query, case_id):
    case = next((c for c in CASES if c["id"] == case_id), None)
    if not case:
        await query.answer("الحالة غير موجودة", show_alert=True)
        return
    q = case.get("quiz", {})
    # build options keyboard
    kb = InlineKeyboardMarkup(row_width=1)
    for idx, opt in enumerate(q.get("options", [])):
        kb.add(InlineKeyboardButton(opt, callback_data=f"answer_{case_id}_{idx}"))
    kb.add(InlineKeyboardButton("⬅️ رجوع للحالة", callback_data=f"case_{case_id}"))
    image_path = BASE_DIR / case["image"]
    try:
        await bot.send_photo(chat_id=query.from_user.id, photo=open(image_path, "rb"),
                             caption=f"*سؤال للاختبار:*\n{q.get('question','سؤال')}",
                             parse_mode="Markdown", reply_markup=kb)
        try:
            await query.message.delete()
        except:
            pass
    except Exception as e:
        logger.exception("failed send quiz image: %s", e)
        try:
            await query.message.edit_text(q.get("question","سؤال"), reply_markup=kb)
        except:
            await bot.send_message(query.from_user.id, q.get("question","سؤال"), reply_markup=kb)
    await query.answer()

async def handle_answer(query, case_id, idx):
    case = next((c for c in CASES if c["id"] == case_id), None)
    if not case:
        await query.answer("الحالة غير موجودة", show_alert=True)
        return
    correct = case.get("quiz", {}).get("answer_index", 0)
    if idx == correct:
        try:
            await query.message.edit_text("✅ صحيح! ممتاز.")
        except:
            await bot.send_message(query.from_user.id, "✅ صحيح! ممتاز.")
    else:
        correct_text = case.get("quiz", {}).get("options", [])[correct]
        try:
            await query.message.edit_text(f"❌ خطأ. الإجابة الصحيحة: *{correct_text}*", parse_mode="Markdown")
        except:
            await bot.send_message(query.from_user.id, f"❌ خطأ. الإجابة الصحيحة: {correct_text}")
    await query.answer()

async def back_main(query):
    kb = main_menu_kb()
    try:
        await query.message.edit_text("رجعنا للقائمة الرئيسية:", reply_markup=kb)
    except:
        await bot.send_message(query.from_user.id, "رجعنا للقائمة الرئيسية:", reply_markup=kb)
    await query.answer()

# handle plain text (for number input)
@dp.message_handler()
async def text_handler(message: types.Message):
    txt = (message.text or "").strip()
    if txt.isdigit():
        num = int(txt)
        if 1 <= num <= len(CASES):
            # send quiz for that case number
            # reuse send_quiz_for_case but we need an artificial CallbackQuery-like object:
            # simpler: directly send quiz content here
            case = next((c for c in CASES if c["id"] == num), None)
            if case:
                q = case.get("quiz", {})
                kb = InlineKeyboardMarkup(row_width=1)
                for idx, opt in enumerate(q.get("options", [])):
                    kb.add(InlineKeyboardButton(opt, callback_data=f"answer_{num}_{idx}"))
                kb.add(InlineKeyboardButton("⬅️ رجوع للحالة", callback_data=f"case_{num}"))
                image_path = BASE_DIR / case["image"]
                try:
                    await bot.send_photo(chat_id=message.chat.id, photo=open(image_path, "rb"),
                                         caption=f"*سؤال للاختبار:*\n{q.get('question','سؤال')}",
                                         parse_mode="Markdown", reply_markup=kb)
                except Exception:
                    await message.reply(q.get('question','سؤال'), reply_markup=kb)
        else:
            await message.reply("رقم غير صالح. ارسل رقم بين 1 و {}".format(len(CASES)))
    else:
        await message.reply("اكتب /start للرجوع للقائمة أو اختر زر من الواجهة.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
