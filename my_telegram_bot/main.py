import telebot
import schedule
import time
import threading
from datetime import datetime, timedelta
import os


TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

user_tasks = {}
user_names = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id not in user_names:
        bot.send_message(user_id, "Привет! Как тебя зовут?")
        bot.register_next_step_handler(message, save_name)
    else:
        bot.send_message(user_id, f"С возвращением, {user_names[user_id]}! Напиши /addtask чтобы добавить задачу.")

def save_name(message):
    user_id = message.from_user.id
    user_names[user_id] = message.text.strip()
    bot.send_message(user_id, f"Приятно познакомиться, {user_names[user_id]}! Напиши /addtask чтобы добавить задачу.")

@bot.message_handler(commands=['addtask'])
def add_task(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "Введите задачу и срок (в формате: Текст задачи | YYYY-MM-DD HH:MM)")
    bot.register_next_step_handler(message, process_task)

def process_task(message):
    user_id = message.from_user.id
    try:
        text, deadline_str = map(str.strip, message.text.split("|"))
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
        task = {"text": text, "deadline": deadline, "notified": False}
        user_tasks.setdefault(user_id, []).append(task)
        bot.send_message(user_id, f"{user_names.get(user_id, 'Друг')}, задача добавлена!")
    except:
        bot.send_message(user_id, "Неверный формат. Повторите /addtask")

@bot.message_handler(commands=['listtasks'])
def list_tasks(message):
    user_id = message.from_user.id
    tasks = user_tasks.get(user_id, [])
    if not tasks:
        bot.send_message(user_id, f"{user_names.get(user_id, 'Друг')}, у тебя нет задач.")
        return
    response = f"{user_names.get(user_id, 'Друг')}, вот твои задачи:\n"
    for i, task in enumerate(tasks, 1):
        deadline_str = task['deadline'].strftime("%Y-%m-%d %H:%M")
        response += f"{i}. {task['text']} (до {deadline_str})\n"
    bot.send_message(user_id, response)

@bot.message_handler(commands=['deletetask'])
def delete_task(message):
    user_id = message.from_user.id
    tasks = user_tasks.get(user_id, [])
    if not tasks:
        bot.send_message(user_id, "У тебя нет задач.")
        return
    bot.send_message(user_id, "Введи номер задачи, которую нужно удалить.")
    bot.register_next_step_handler(message, process_delete_task)

def process_delete_task(message):
    user_id = message.from_user.id
    try:
        index = int(message.text.strip()) - 1
        if 0 <= index < len(user_tasks[user_id]):
            removed = user_tasks[user_id].pop(index)
            bot.send_message(user_id, f"Удалена задача: {removed['text']}")
        else:
            bot.send_message(user_id, "Неверный номер задачи.")
    except:
        bot.send_message(user_id, "Ошибка. Введи правильный номер.")

@bot.message_handler(commands=['edittask'])
def edit_task(message):
    user_id = message.from_user.id
    tasks = user_tasks.get(user_id, [])
    if not tasks:
        bot.send_message(user_id, "У тебя нет задач.")
        return
    bot.send_message(user_id, "Введи номер задачи, которую хочешь изменить.")
    bot.register_next_step_handler(message, process_edit_index)

def process_edit_index(message):
    user_id = message.from_user.id
    try:
        index = int(message.text.strip()) - 1
        if 0 <= index < len(user_tasks[user_id]):
            message.bot.edit_index = index
            bot.send_message(user_id, "Введи новую задачу и срок (в формате: Текст | YYYY-MM-DD HH:MM)")
            bot.register_next_step_handler(message, process_edit_task)
        else:
            bot.send_message(user_id, "Неверный номер задачи.")
    except:
        bot.send_message(user_id, "Ошибка. Введи правильный номер.")

def process_edit_task(message):
    user_id = message.from_user.id
    index = message.bot.edit_index
    try:
        text, deadline_str = map(str.strip, message.text.split("|"))
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
        user_tasks[user_id][index] = {"text": text, "deadline": deadline, "notified": False}
        bot.send_message(user_id, f"{user_names.get(user_id, 'Друг')}, задача обновлена.")
    except:
        bot.send_message(user_id, "Неверный формат. Повторите /edittask")

def check_deadlines():
    now = datetime.now()
    for user_id, tasks in user_tasks.items():
        for task in tasks:
            if not task["notified"] and now >= task["deadline"]:
                bot.send_message(user_id, f"{user_names.get(user_id, 'Друг')}, срок задачи '{task['text']}' истёк!")
                task["notified"] = True

def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(1)

schedule.every(60).seconds.do(check_deadlines)

threading.Thread(target=schedule_checker).start()

bot.polling(none_stop=True)
