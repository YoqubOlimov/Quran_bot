import asyncio
import os
import re
import aiohttp
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
API_URL = "https://api.alquran.cloud/v1/surah/{}/en.asad"
PRAYER_TIMES_API = "http://api.aladhan.com/v1/timingsByCity?city=Tashkent&country=Uzbekistan&method=2"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

dp.include_router(router)


class RegisterState(StatesGroup):
    name = State()
    surname = State()
    phone = State()


@router.message(Command("start"))
async def ask_name(message: types.Message, state: FSMContext):
    await message.answer("Ro‘yxatdan o‘tish uchun ismingizni kiriting:")
    await state.set_state(RegisterState.name)


@router.message(RegisterState.name)
async def ask_surname(message: types.Message, state: FSMContext):
    if not re.match(r'^[A-Za-z\'\-]+$', message.text):
        await message.answer("Iltimos, to‘g‘ri ism kiriting!")
        return
    await state.update_data(name=message.text)
    await message.answer("Familiyangizni kiriting:")
    await state.set_state(RegisterState.surname)


@router.message(RegisterState.surname)
async def ask_phone(message: types.Message, state: FSMContext):
    if not re.match(r'^[A-Za-z\'\-]+$', message.text):
        await message.answer("Iltimos, to‘g‘ri familiya kiriting!")
        return
    await state.update_data(surname=message.text)
    phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Telefon raqamni yuborish", request_contact=True)]
    ],
        resize_keyboard=True
    )
    await message.answer("Telefon raqamingizni yuboring:", reply_markup=phone_keyboard)
    await state.set_state(RegisterState.phone)


@router.message(RegisterState.phone, F.contact)
async def finish_registration(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    data = await state.get_data()
    await message.answer(
        f"Ro‘yxatdan o‘tdingiz!\nIsm: {data['name']}\nFamiliya: {data['surname']}\nTelefon: {data['phone']}"
    )
    await state.clear()
    main_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Qidiruv"), KeyboardButton(text="Namoz vaqti")]
        ],
        resize_keyboard=True
    )

    await message.answer("Quyidagi menyudan tanlang:", reply_markup=main_menu)


@router.message(F.text == "Namoz vaqti")
async def namoz_vaqti_menu(message: types.Message):
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Bomdod", callback_data="Fajr")],
            [InlineKeyboardButton(text="Peshin", callback_data="Dhuhr")],
            [InlineKeyboardButton(text="Asr", callback_data="Asr")],
            [InlineKeyboardButton(text="Shom", callback_data="Maghrib")],
            [InlineKeyboardButton(text="Xufton", callback_data="Isha")]
        ]
    )
    await message.answer("Qaysi namoz vaqtini bilmoqchisiz?", reply_markup=inline_kb)


@router.callback_query(F.data.in_({"Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"}))
async def send_prayer_time(callback: types.CallbackQuery):
    prayer_time = callback.data
    async with aiohttp.ClientSession() as session:
        async with session.get(PRAYER_TIMES_API) as response:
            if response.status == 200:
                data = await response.json()
                timings = data["data"]["timings"]
                await callback.message.answer(f"{prayer_time} vaqti: {timings[prayer_time]}")
            else:
                await callback.message.answer("Xatolik yuz berdi, iltimos keyinroq urinib ko'ring.")


@router.message(F.text == "Qidiruv")
async def search_surah(message: types.Message):
    await message.answer("Qaysi surani qidiryapsiz? Suraning raqamini kiriting:")


@router.message(F.text.regexp(r'^\d+$'))
async def get_surah(message: types.Message):
    surah_number = message.text
    url = API_URL.format(surah_number)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("data"):
                    surah_name = data["data"].get("englishName", "Noma'lum")
                    await message.answer(f"Surah: {surah_name}")
                else:
                    await message.answer("Xatolik yuz berdi yoki sura topilmadi!")
            else:
                await message.answer("Xatolik yuz berdi yoki sura topilmadi!")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
