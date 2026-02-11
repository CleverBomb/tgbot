import asyncio
import random
import difflib

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from docx import Document

# ---------------- КОНФИГУРАЦИЯ ----------------
# Токеніңізді осында қалдырыңыз
TOKEN = "token here"

# ---------------- ЗАГРУЗКА 500 СЛОВ ИЗ DOCX ----------------
def load_slang_from_docx(path: str):
    slang = {}
    try:
        doc = Document(path)
        current_category = "Жалпы"

        for p in doc.paragraphs:
            line = p.text.strip()
            if not line: continue
            low = line.lower()

            # Категорияларды анықтау
            if "адам сипаттамасына" in low: current_category = "👤 Адам сипаттамасы"
            elif "эмоция" in low: current_category = "🌈 Эмоция"
            elif "интернет және әлеуметтік" in low: current_category = "🌐 Интернет"
            elif "ойын сленгтері" in low: current_category = "🎮 Ойын"
            elif "оқу сленгтері" in low: current_category = "📚 Оқу"
            elif "қарым-қатынас және орта" in low: current_category = "🤝 Орта"
            elif "медиа" in low: current_category = "🎬 Медиа"
            elif "техникалық" in low: current_category = "💻 Техно"
            elif "мәдениет" in low: current_category = "🎨 Мәдениет"

            # Сөз бен мағынаны бөлу
            if "—" in line:
                parts = line.split("—", 1)
                word = parts[0].strip().lower()
                meaning = parts[1].strip()
                slang[word] = (meaning, current_category)
    except Exception as e:
        print(f"Файлды оқу қатесі: {e}")
    return slang

# Сөздікті жүктеу
SLANG_DICT = load_slang_from_docx("сленгтер сөздігі 500 сөз.docx")

# ---------------- ПЕРНЕПЛАША (KEYBOARD) ----------------
def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    # Кездейсоқ сөз алу батырмасы
    builder.button(text="🎲 Кездейсоқ сөз алу", callback_data="random_word")
    builder.adjust(1)
    return builder.as_markup()

# ---------------- ХЕНДЛЕРЛЕР ----------------
dp = Dispatcher()

@dp.message(CommandStart())
async def start_command(message: types.Message):
    user_name = message.from_user.first_name
    text = (
        f"🇰🇿 <b>Сәлем, {user_name}!</b>\n\n"
        f"🤖 <b>Мен — QazaqSlang ботымын!</b>\n"
        f"Заманауи қазақ жастарының сленгін түсінуге көмектесемін.\n\n"
        f"😎 <b>Мен не істей аламын?</b>\n"
        f"🔹 Сөздердің мағынасын түсіндіріп, санатын көрсетемін.\n"
        f"🔹 Менде <b>{len(SLANG_DICT)}</b> сленг сөз бар.\n"
        f"🔹 Кездейсоқ жаңа сөздерді үйретемін.\n\n"
        f"📂 <b>Негізгі санаттар:</b>\n"
        f"👤 <i>Адам сипаттамасы,</i> 🌈 <i>Эмоция,</i> 🌐 <i>Интернет,</i>\n"
        f"🎮 <i>Ойын,</i> 📚 <i>Оқу,</i> 🤝 <i>Орта,</i> 💻 <i>IT.</i>\n\n"
        f"🚀 <b>Бастау үшін:</b>\n"
        f"Сөзді жазыңыз немесе төмендегі батырманы басыңыз! 👇"
    )
    await message.answer(text, reply_markup=get_main_keyboard())

# КЕЗДЕЙСОҚ СӨЗ БАТЫРМАСЫ ЖҰМЫСЫ
@dp.callback_query(F.data == "random_word")
async def callback_random(callback: types.CallbackQuery):
    if not SLANG_DICT:
        await callback.answer("Сөздік бос!", show_alert=True)
        return

    # Сөздіктен кездейсоқ бір сөзді таңдау
    word, data = random.choice(list(SLANG_DICT.items()))
    meaning, category = data

    text = (
        f"🎲 <b>Кездейсоқ таңдалған сленг:</b>\n\n"
        f"✨ <b>{word.upper()}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📝 <b>Мағынасы:</b> {meaning}\n"
        f"📂 <b>Санаты:</b> {category}"
    )

    # Хабарламаны жаңартып, батырманы қайта шығару
    await callback.message.edit_text(text, reply_markup=get_main_keyboard())
    # Батырма басылғаны туралы сигналды жабу
    await callback.answer()

@dp.message(F.text)
async def translate_slang(message: types.Message):
    user_word = message.text.lower().strip()

    if user_word in SLANG_DICT:
        meaning, category = SLANG_DICT[user_word]
        await message.answer(
            f"✅ <b>{user_word.capitalize()}</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📖 <b>Мағынасы:</b> {meaning}\n"
            f"📂 <b>Санаты:</b> {category}",
            reply_markup=get_main_keyboard()
        )
    else:
        # Ұқсас сөздерді іздеу
        matches = difflib.get_close_matches(user_word, SLANG_DICT.keys(), n=1, cutoff=0.6)
        if matches:
            suggested = matches[0]
            meaning, category = SLANG_DICT[suggested]
            await message.answer(
                f"🤔 Мүмкін сіз <b>{suggested}</b> сөзін іздедіңіз бе?\n\n"
                f"👉 {suggested.capitalize()} — {meaning}\n"
                f"📂 Санаты: {category}",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                "❌ Кешіріңіз, бұл сөз табылмады. Басқа сөз жазып көріңіз немесе 'random' батырмасын басыңыз.",
                reply_markup=get_main_keyboard()
            )

# ---------------- ІСКЕ ҚОСУ ----------------
async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    print(f"🚀 Бот іске қосылды. Сөздер саны: {len(SLANG_DICT)}")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())