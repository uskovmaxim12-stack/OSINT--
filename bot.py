import asyncio
import logging
import subprocess
import shlex
import tempfile
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN, ALLOWED_USERS, SHERLOCK_PATH

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Инициализация бота и диспетчера ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Обработчик команды /start ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("👋 Привет! Я OSINT-бот для поиска информации.\n\n"
                         "Отправь мне команду `/search <username>` или "
                         "`/mail <email>` для поиска.\n\n"
                         "⚠️ Используй меня только в образовательных целях!",
                         parse_mode="Markdown")

# --- Обработчик команды /search ---
@dp.message(Command("search"))
async def cmd_search(message: types.Message):
    # 1. Проверка авторизации (белый список)
    if str(message.from_user.id) not in ALLOWED_USERS:
        await message.answer("🚫 У вас нет доступа к этому боту.")
        return

    # 2. Получение username из команды
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажите username для поиска.\nПример: `/search janedoe`", parse_mode="Markdown")
        return
    username = args[1].strip()

    # 3. Уведомление о начале поиска
    status_msg = await message.answer(f"🔍 Начинаю поиск для `{username}`...\nЭто может занять некоторое время.", parse_mode="Markdown")

    # 4. Выполнение поиска через Sherlock
    try:
        # Создаем временный файл для отчета
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tmp_file:
            report_path = tmp_file.name

        # Запускаем Sherlock. Используем shlex.quote для экранирования username.
        # Команда: sherlock username --output /path/to/report.txt
        cmd = f"cd {shlex.quote(SHERLOCK_PATH)} && python -m sherlock {shlex.quote(username)} --output {shlex.quote(report_path)}"
        logger.info(f"Running command: {cmd}")

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode('utf-8')
            logger.error(f"Sherlock failed: {error_msg}")
            await status_msg.edit_text(f"❌ Ошибка при выполнении поиска для `{username}`.\nВозможно, имя не найдено или проблема с сетью.", parse_mode="Markdown")
            # Попробуем удалить временный файл в случае ошибки
            try:
                os.unlink(report_path)
            except:
                pass
            return

        # 5. Отправка результата
        # Sherlock создает файл с результатами.
        # Проверяем, существует ли файл и не пустой ли он.
        if os.path.exists(report_path) and os.path.getsize(report_path) > 0:
            # Читаем отчет
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
            
            # Если отчет слишком большой, отправляем файлом
            if len(report_content) > 4000:
                await message.answer_document(
                    types.input_file.FSInputFile(report_path, filename=f"{username}_report.txt"),
                    caption=f"📄 Отчет по запросу `{username}`.", parse_mode="Markdown"
                )
                await status_msg.delete()
            else:
                await status_msg.edit_text(f"✅ Результат поиска для `{username}`:\n\n```\n{report_content}```", parse_mode="Markdown")
        else:
            await status_msg.edit_text(f"❌ Не найдено ни одного публичного профиля для `{username}`.", parse_mode="Markdown")

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        await status_msg.edit_text("⚠️ Произошла непредвиденная внутренняя ошибка.")
    finally:
        # Удаляем временный файл
        try:
            if os.path.exists(report_path):
                os.unlink(report_path)
        except:
            pass

# --- Запуск бота ---
async def main():
    logger.info("Starting OSINT bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
