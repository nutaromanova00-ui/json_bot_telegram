import json
import logging
import re
from typing import Tuple, Optional
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from flask import Flask
app = Flask('')
@app.route('/')
def home():
    return "✅ JSON бот работает!"

def run_web():
    app.run(host='0.0.0.0', port=8080)
    
# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # ВНИМАНИЕ: Замените на ваш токен!

def find_and_explain_error(json_text: str) -> str:
    """Находит ошибку и понятно объясняет её"""
    
    # Проверка 1: Одинарные кавычки
    if "'" in json_text:
        return """
❌ ОШИБКА: Использованы одинарные кавычки

📝 ЧТО НЕ ТАК: В JSON можно использовать только двойные кавычки

🔧 КАК ИСПРАВИТЬ: Замените все одинарные кавычки на двойные

✅ ПРАВИЛЬНО:
{"name": "John", "age": 30}

❌ НЕПРАВИЛЬНО:
{'name': 'John', 'age': 30}
"""
    
    # Проверка 2: Ключи без кавычек
    if re.search(r'\{?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', json_text):
        return """
❌ ОШИБКА: Ключ (название поля) не в кавычках

📝 ЧТО НЕ ТАК: Все ключи в JSON должны быть в двойных кавычках

🔧 КАК ИСПРАВИТЬ: Возьмите название ключа в двойные кавычки

✅ ПРАВИЛЬНО:
{"name": "John", "age": 30}

❌ НЕПРАВИЛЬНО:
{name: "John", age: 30}
"""
    
    # Проверка 3: Лишняя запятая
    if ',}' in json_text:
        return """
❌ ОШИБКА: Лишняя запятая перед закрывающей скобкой

📝 ЧТО НЕ ТАК: После последнего элемента в объекте не нужна запятая

🔧 КАК ИСПРАВИТЬ: Удалите запятую перед закрывающей скобкой

✅ ПРАВИЛЬНО:
{"name": "John", "age": 30}

❌ НЕПРАВИЛЬНО:
{"name": "John", "age": 30,}
"""
    
    # Проверка 4: Незакрытая строка
    if json_text.count('"') % 2 != 0:
        return """
❌ ОШИБКА: Незакрытая строка

📝 ЧТО НЕ ТАК: У вас есть открывающая кавычка, но нет закрывающей

🔧 КАК ИСПРАВИТЬ: Добавьте закрывающую кавычку в конце строки

✅ ПРАВИЛЬНО:
{"name": "John"}

❌ НЕПРАВИЛЬНО:
{"name": "John
"""
    
    # Проверка 5: Пропущено двоеточие
    if re.search(r'"[^"]+"\s+"[^"]+"', json_text):
        return """
❌ ОШИБКА: Пропущено двоеточие между ключом и значением

📝 ЧТО НЕ ТАК: Между ключом и значением должно быть двоеточие

🔧 КАК ИСПРАВИТЬ: Поставьте двоеточие между ключом и значением

✅ ПРАВИЛЬНО:
{"name": "John", "age": 30}

❌ НЕПРАВИЛЬНО:
{"name" "John", "age" 30}
"""
    
    # Проверка 6: Неправильные скобки
    open_braces = json_text.count('{')
    close_braces = json_text.count('}')
    
    if open_braces != close_braces:
        if open_braces > close_braces:
            diff = open_braces - close_braces
            return f"""
❌ ОШИБКА: Не хватает закрывающих скобок

📝 ЧТО НЕ ТАК: У вас открыто больше скобок, чем закрыто

🔧 КАК ИСПРАВИТЬ: Добавьте {diff} закрывающую скобку в конец

✅ ПРАВИЛЬНО:
{{"name": "John"}}

❌ НЕПРАВИЛЬНО:
{{"name": "John"
"""
        else:
            diff = close_braces - open_braces
            return f"""
❌ ОШИБКА: Лишние закрывающие скобки

📝 ЧТО НЕ ТАК: У вас больше закрывающих скобок, чем открывающих

🔧 КАК ИСПРАВИТЬ: Удалите {diff} лишнюю закрывающую скобку

✅ ПРАВИЛЬНО:
{{"name": "John"}}
"""
    
    # Проверка 7: Проблема с запятыми между элементами
    if re.search(r'"[^"]+"\s+"[^"]+"', json_text) and ':' in json_text:
        return """
❌ ОШИБКА: Пропущена запятая между элементами

📝 ЧТО НЕ ТАК: Элементы в объекте нужно разделять запятыми

🔧 КАК ИСПРАВИТЬ: Поставьте запятую между элементами

✅ ПРАВИЛЬНО:
{"name": "John", "age": 30}

❌ НЕПРАВИЛЬНО:
{"name": "John" "age": 30}
"""
    
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """🤖 JSON ПОМОЩНИК

Отправьте мне JSON, и я:
- Найду все ошибки
- Понятно объясню, что не так
- Покажу правильный вариант

ПРИМЕРЫ ПРАВИЛЬНОГО JSON:

1. Простой объект:
{"name": "Анна", "age": 25}

2. С вложением:
{"user": {"name": "Иван"}, "active": true}

3. С массивом:
{"hobbies": ["чтение", "музыка"]}

ОТПРАВЬТЕ МНЕ ВАШ JSON ДЛЯ ПРОВЕРКИ"""
    await update.message.reply_text(text)

async def handle_json(update: Update, context: ContextTypes.DEFAULT_TYPE):
    json_text = update.message.text.strip()
    
    await update.message.reply_text("🔍 Проверяю JSON...")
    
    # Пробуем распарсить JSON
    try:
        parsed = json.loads(json_text)
        formatted = json.dumps(parsed, indent=2, ensure_ascii=False, sort_keys=True)
        
        await update.message.reply_text(
            f"✅ JSON ПРАВИЛЬНЫЙ!\n\nОтформатированный вариант:\n```json\n{formatted}\n```",
            parse_mode='Markdown'
        )
        
    except json.JSONDecodeError as e:
        # Сначала ищем типичные ошибки
        explanation = find_and_explain_error(json_text)
        
        if explanation:
            await update.message.reply_text(explanation)
        else:
            # Если типичная ошибка не найдена, показываем позицию
            error_line = e.lineno
            error_col = e.colno
            lines = json_text.split('\n')
            
            error_text = f"""❌ ОШИБКА В JSON

ТИП ОШИБКИ: {e.msg}

МЕСТО ОШИБКИ: строка {error_line}, позиция {error_col}

ПРОБЛЕМНАЯ СТРОКА:
{lines[error_line-1] if error_line <= len(lines) else 'Не найдена'}

ПОСМОТРИТЕ ВНИМАТЕЛЬНО НА ЭТО МЕСТО В ВАШЕМ JSON

ОБЫЧНЫЕ ПРИЧИНЫ:
- Пропущена кавычка
- Пропущена запятая
- Пропущено двоеточие
- Лишний символ"""
            await update.message.reply_text(error_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """ЧАСТЫЕ ОШИБКИ В JSON:

1. ОДИНАРНЫЕ КАВЫЧКИ
❌ {'name': 'John'}
✅ {"name": "John"}

2. КЛЮЧИ БЕЗ КАВЫЧЕК
❌ {name: "John"}
✅ {"name": "John"}

3. ЛИШНЯЯ ЗАПЯТАЯ
❌ {"name": "John",}
✅ {"name": "John"}

4. НЕЗАКРЫТАЯ СТРОКА
❌ {"name": "John}
✅ {"name": "John"}

5. ПРОПУЩЕНО ДВОЕТОЧИЕ
❌ {"name" "John"}
✅ {"name": "John"}

6. НЕПРАВИЛЬНЫЕ СКОБКИ
❌ {"name": "John"
✅ {"name": "John"}"""
    await update.message.reply_text(text)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_json))
    
    print("🤖 JSON бот запущен!")
    print("Бот будет понятно объяснять ошибки")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
