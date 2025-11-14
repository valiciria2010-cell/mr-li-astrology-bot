import os
import logging
from datetime import datetime
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class ChineseAstrologyAI:
    def __init__(self):
        self.animals = ["Крыса", "Бык", "Тигр", "Кролик", "Дракон", "Змея", 
                       "Лошадь", "Коза", "Обезьяна", "Петух", "Собака", "Свинья"]
        self.elements = ["Дерево", "Огонь", "Земля", "Металл", "Вода"]
        
    def get_animal(self, year):
        start_year = 1900
        index = (year - start_year) % 12
        return self.animals[index]
    
    def get_element(self, year):
        start_year = 1900
        index = ((year - start_year) // 2) % 5
        return self.elements[index]
    
    def calculate_compatibility(self, year1, year2):
        animal1 = self.get_animal(year1)
        animal2 = self.get_animal(year2)
        element1 = self.get_element(year1)
        element2 = self.get_element(year2)
        
        # Простая логика совместимости (можно расширить)
        animal_comp = self._animal_compatibility(animal1, animal2)
        element_comp = self._element_compatibility(element1, element2)
        
        total_score = (animal_comp['score'] + element_comp['score']) / 2
        
        return {
            'animals': [animal1, animal2],
            'elements': [element1, element2],
            'total_score': total_score,
            'animal_compatibility': animal_comp,
            'element_compatibility': element_comp
        }
    
    def _animal_compatibility(self, animal1, animal2):
        # Базовая логика - можно добавить вашу базу знаний
        compatibility_rules = {
            "Крыса": {"best": ["Дракон", "Обезьяна"], "good": ["Бык"], "bad": ["Лошадь"]},
            "Дракон": {"best": ["Крыса", "Обезьяна", "Петух"], "good": ["Змея", "Тигр"], "bad": ["Собака", "Бык"]},
            # Добавьте правила для всех животных
        }
        
        score = 70
        if animal2 in compatibility_rules.get(animal1, {}).get("best", []):
            score = 90
        elif animal2 in compatibility_rules.get(animal1, {}).get("good", []):
            score = 80
        elif animal2 in compatibility_rules.get(animal1, {}).get("bad", []):
            score = 50
            
        return {"score": score, "description": f"Сочетание {animal1} и {animal2}"}
    
    def _element_compatibility(self, elem1, elem2):
        element_cycles = {
            "Дерево": {"support": "Вода", "control": "Земля"},
            "Огонь": {"support": "Дерево", "control": "Вода"},
            "Земля": {"support": "Огонь", "control": "Дерево"},
            "Металл": {"support": "Земля", "control": "Огонь"},
            "Вода": {"support": "Металл", "control": "Земля"}
        }
        
        if elem2 == element_cycles[elem1]["support"]:
            return {"score": 85, "relationship": "Поддерживающая"}
        elif elem2 == element_cycles[elem1]["control"]:
            return {"score": 60, "relationship": "Контролирующая"}
        else:
            return {"score": 75, "relationship": "Нейтральная"}

class MrLiAstrologyBot:
    def __init__(self, token):
        self.token = token
        self.astrology_ai = ChineseAstrologyAI()
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        welcome_text = f"""
🎎 Здравствуйте, {user.first_name}! Я - Мистер Ли, ваш консультант по вопросам брака на основе восточного гороскопа.

🪷 Моя семья уже 5 поколений помогает парам обрести гармонию в отношениях.

📝 Для анализа совместимости введите ваш год рождения (например: 1985):
        """
        await update.message.reply_text(welcome_text)
        context.user_data['step'] = 'awaiting_user_year'

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_data = context.user_data
        text = update.message.text.strip()
        
        try:
            if user_data.get('step') == 'awaiting_user_year':
                await self._handle_user_year(update, context, text)
            elif user_data.get('step') == 'awaiting_partner_year':
                await self._handle_partner_year(update, context, text)
        except Exception as e:
            logging.error(f"Ошибка: {e}")
            await update.message.reply_text("⚠️ Произошла ошибка. Давайте начнем заново. Введите /start")

    async def _handle_user_year(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        try:
            year = int(text)
            if year < 1900 or year > datetime.now().year:
                await update.message.reply_text("⚠️ Пожалуйста, введите реальный год рождения (1900-2024):")
                return
                
            context.user_data['user_year'] = year
            context.user_data['step'] = 'awaiting_partner_year'
            
            animal = self.astrology_ai.get_animal(year)
            element = self.astrology_ai.get_element(year)
            
            response = f"""
✅ Ваши данные записаны:
• Год рождения: {year}
• Животное: {animal}
• Стихия: {element}

📝 Теперь введите год рождения партнера:
            """
            await update.message.reply_text(response)
            
        except ValueError:
            await update.message.reply_text("⚠️ Пожалуйста, введите год цифрами (например: 1990):")

    async def _handle_partner_year(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        try:
            year = int(text)
            if year < 1900 or year > datetime.now().year:
                await update.message.reply_text("⚠️ Пожалуйста, введите реальный год рождения:")
                return
                
            user_year = context.user_data['user_year']
            
            analyzing_msg = await update.message.reply_text("🔮 Мистер Ли анализирует вашу совместимость...")
            
            compatibility_data = self.astrology_ai.calculate_compatibility(user_year, year)
            
            await analyzing_msg.delete()
            
            report = self._generate_report(compatibility_data, user_year, year)
            await update.message.reply_text(report, parse_mode='HTML')
            
            context.user_data['step'] = 'awaiting_user_year'
            
            await update.message.reply_text("🔄 Хотите проанализировать другую пару? Введите ваш год рождения:")
            
        except ValueError:
            await update.message.reply_text("⚠️ Пожалуйста, введите год цифрами:")

    def _generate_report(self, data, year1, year2):
        animal1, animal2 = data['animals']
        element1, element2 = data['elements']
        
        report = f"""
🎎 <b>АНАЛИЗ СОВМЕСТИМОСТИ ОТ МИСТЕРА ЛИ</b>

👤 <b>Ваши данные:</b>
• Ваш год: {year1} (<b>{animal1}</b>, {element1})
• Партнер: {year2} (<b>{animal2}</b>, {element2})

💫 <b>ОБЩАЯ СОВМЕСТИМОСТЬ: {data['total_score']:.0f}%</b>

📊 <b>Детальный анализ:</b>
• Совместимость животных: {data['animal_compatibility']['score']}%
• Совместимость стихий: {data['element_compatibility']['score']}%
• Отношения стихий: {data['element_compatibility']['relationship']}

🪷 <b>Духовные практики для гармонии:</b>
• Медитация "Единство сердец" - 15 минут утром
• Практика благодарности перед сном
• Совместный цигун в полнолуние

💝 <i>«Истинная гармония приходит через взаимопонимание»</i>
- <b>Мистер Ли</b>
        """
        return report

def main():
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        logging.error("❌ BOT_TOKEN не установлен!")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    bot = MrLiAstrologyBot(BOT_TOKEN)
    
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    logging.info("🟢 Бот 'Мистер Ли' запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
