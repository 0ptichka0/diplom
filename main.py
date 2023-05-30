import aiogram
import sqlite3
import logging
import requests
import json
import asyncio
import typing
import psycopg2
import datetime

from aiogram.bot import api
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
from aiogram.contrib.middlewares.logging import  LoggingMiddleware

import aiogram.utils.markdown as md
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram.types import ParseMode

from settings import dp, bot, connection
import SQLfile as s

"""
________________________________________________________________________________________________________________________________________________________________________________
                                                                                        user start
________________________________________________________________________________________________________________________________________________________________________________
"""

button_verefication = InlineKeyboardButton("Начать верефикацию", callback_data="vereficateon")
keyboard_primer1 = InlineKeyboardMarkup().row(button_verefication)

button_primer2 = InlineKeyboardButton("В меню", callback_data="menu")
keyboard_primer2 = InlineKeyboardMarkup().row(button_primer2)



@dp.callback_query_handler(text="vereficateon")
async def GoMenu(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    ansver = await s.New_unregister_user(query.message, connection)
    if ansver:
        await query.message.answer(f"Начало верефикации\n\nДля вашего индифицирования подойдите на вахту и покажите ваш индивидуадбный номер\nВаш номер: #{query.message.chat.id}")
    else:
        await Menu(query.message)


"""
________________________________________________________________________________________________________________________________________________________________________________
                                                                                        commands
________________________________________________________________________________________________________________________________________________________________________________
"""

@dp.message_handler(commands=['start'])
async def Start_Bot_comm(message: types.Message):
    await message.answer("Добро поджаловать в бота 'СБДРПО'\n\nДля продолжения работы нажмите на кнопку 'Начать верефикацию' ниже", reply_markup=keyboard_primer1)

@dp.message_handler(commands=['menu'])
async def menu_comm(message: types.Message):
    await Menu(message)

@dp.message_handler(commands=['reg'])
async def Auto_reg_user_comm(message: types.Message):
    ansver = await s.Reg_user(message, message.chat.id)
    if ansver:
        await message.answer(f"Пользователь индифицирован!\n\nДобро пожаловать в систему @{message.chat.username}", reply_markup=keyboard_primer2)
    else:
        await message.answer("Вы уже зарегстрированны")
        await Menu(message)

@dp.message_handler(commands=['swap_watch'])
async def Auto_reg_user_comm(message: types.Message):
    await Role_swap(message, await s.Check_user_privileges(message), "watch")

@dp.message_handler(commands=['swap_user'])
async def Auto_reg_user_comm(message: types.Message):
    await Role_swap(message, await s.Check_user_privileges(message), "user")

@dp.message_handler(commands=['swap_AHS'])
async def Auto_reg_user_comm(message: types.Message):
    await Role_swap(message, await s.Check_user_privileges(message), "AHS")


async def Role_swap(message, now, new):
    if now == "user":
        insert_query = (f'SELECT id, name, token FROM public."Users" where id = {message.chat.id};')
        cursor = connection.cursor()
        cursor.execute(insert_query)
        result = cursor.fetchall()[0]
        insert_query2 = (f'DELETE FROM public."Users" where id = {message.chat.id};')
        cursor = connection.cursor()
        cursor.execute(insert_query2)
    elif now == "watch":
        insert_query = (f'SELECT id, name, token FROM public."Watch" where id = {message.chat.id};')
        cursor = connection.cursor()
        cursor.execute(insert_query)
        result = cursor.fetchall()[0]
        insert_query2 = (f'DELETE FROM public."Watch" where id = {message.chat.id};')
        cursor = connection.cursor()
        cursor.execute(insert_query2)
    elif now == "AHS":
        insert_query = (f'SELECT id, name, token FROM public."AHS" where id = {message.chat.id};')
        cursor = connection.cursor()
        cursor.execute(insert_query)
        result = cursor.fetchall()[0]
        insert_query2 = (f'DELETE FROM public."AHS" where id = {message.chat.id};')
        cursor = connection.cursor()
        cursor.execute(insert_query2)

    if new == "user":
        insert_query = (f'INSERT INTO public."Users" ("id", "name", "token", "room", "status") VALUES (%s, %s, %s, %s, %s);')
        cursor = connection.cursor()
        cursor.execute(insert_query, [result[0], result[1], result[2], 0, 0])
    elif new == "watch":
        insert_query = (f'INSERT INTO public."Watch" ("id", "name", "real_name", "token", "status") VALUES (%s, %s, %s, %s, %s);')
        cursor = connection.cursor()
        cursor.execute(insert_query, [result[0], result[1], "no_name", result[2], 0])
    elif new == "AHS":
        insert_query = (f'INSERT INTO public."AHS" ("id", "name", "token") VALUES (%s, %s, %s);')
        cursor = connection.cursor()
        cursor.execute(insert_query, [result[0], result[1], result[2]])

    await Menu(message)

"""
________________________________________________________________________________________________________________________________________________________________________________
                                                                                        menu
________________________________________________________________________________________________________________________________________________________________________________
"""

@dp.callback_query_handler(text="menu")
async def GoMenu(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await Menu(query.message)

AHS_turn_trable = CallbackData("turn_trab", "namb_trable", "trable")

async def Menu(message: types.Message):
    """
    Главное еню программы
    Определяет какой актор перед ней и выдает нужное контекстное меню
    :param message:
    :return:
    """

    user = await s.Check_user_privileges(message)

    if user == "user":
        bt1 = InlineKeyboardButton("Репорт", callback_data="Report")
        bt2 = InlineKeyboardButton("Доска объявлений", callback_data="bt2")
        bt3 = InlineKeyboardButton("Занять комнату", callback_data="booking")
        bt4 = InlineKeyboardButton("Написать вахте", callback_data="mess")
        bt5 = InlineKeyboardButton("О боте", callback_data="info")
        bt6 = InlineKeyboardButton("Удалить аккаунт", callback_data="del_akk")
        keyboard_menu = InlineKeyboardMarkup().row(bt1, bt2).row(bt3, bt4).row(bt5, bt6)
        await message.answer("Главное меню User", reply_markup=keyboard_menu)

    elif user == "watch":
        status = await s.Check_work_status_watch(message)
        if status == 0:
            button_status = InlineKeyboardButton("Начать работу", callback_data="status_swich")
            keyboard_menu_watch = InlineKeyboardMarkup().row(button_status)
            status = "Не на работе"
        elif status == 1:
            button_status = InlineKeyboardButton("Закончить работу", callback_data="status_swich")
            keyboard_menu_watch = InlineKeyboardMarkup().row(button_status,
                InlineKeyboardButton("Верификация", callback_data="vereficateon_unreg")).row(
                InlineKeyboardButton("Запросы", callback_data="requests"),
                InlineKeyboardButton("Доска объявлений", callback_data="btw3")).row(
                InlineKeyboardButton("Написать объявление", callback_data="btw4"))
            status = "На работе"
        else:
            await message.answer("Неизвесная ошибка! Обратитесь к администратору сети")
            return 0



        await message.answer("Главное меню\n\n"
                             f"Cтатус: <b>{status}</b>\n"
                                 f"Watch", reply_markup=keyboard_menu_watch,
                             parse_mode=types.ParseMode.HTML)


    elif user == "AHS":


        batton_turn_trable = InlineKeyboardButton("Начать работу", callback_data=AHS_turn_trable.new(namb_trable=-1, trable="no"))
        keyboard_turn_trable = InlineKeyboardMarkup().add(batton_turn_trable)
        await message.answer("Главное меню \n\n AHS", reply_markup=keyboard_turn_trable)
    else:
        await message.answer("У вас покачто нет доступа к данному боту")

"""
________________________________________________________________________________________________________________________________________________________________________________
                                                                                        info USER
________________________________________________________________________________________________________________________________________________________________________________
"""

@dp.callback_query_handler(text="info")
async def Bt5(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await query.message.answer("О боте\n\n"
                               "Данный бот предназначен для оперативной работы административно-хозяйственной структуры общежития."
                               "Бот представляет седующие возможности:\n"
                               "1. Оперативно сообщать о проблемах с сантехникой, электрикой и ключами в меню 'Report'\n"
                               "2. Смотреть расписание и занимать комнаты общего назначения в меню 'Занять комнату'\n"
                               "3. Использовать обявления в меню 'Доска объявлений' для поиска потерянных вещей или вещей отдающихся на общее благо\n"
                               "4. Написать о проблеме на вахту в меню 'Написать вахте' для оперативного решения локальных проблем с жителями общеития или для ответа на вопросы проживающих\n\n"
                               "Бот 'СППвО общежития' работает на ваше благо!")
    await Menu(query.message)


"""
________________________________________________________________________________________________________________________________________________________________________________
                                                                                        report a problem USER
________________________________________________________________________________________________________________________________________________________________________________
"""



@dp.callback_query_handler(text="Report")
async def ReportQ(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await Report(query.message)

class Rep(StatesGroup):
    place = State()
    description = State()

async def Report(message: types.Message):
    await message.answer("Введите место проблемы (блок, комната или наименование комнаты)")
    await Rep.place.set()


@dp.message_handler(state=Rep.place)
async def Rep1(message: types.Message, state: FSMContext):
    await state.update_data(place=message.message_id)
    await message.answer("Опешите проблему")
    await Rep.next()

User_data_save = CallbackData("rep_yes", "place", "description")

@dp.message_handler(state=Rep.description)
async def Rep1(message: types.Message, state: FSMContext):
    """
    Заявлка report a problem заполнена и ожидает подтверждения
    :param message:
    :param state:
    :return:
    """
    await state.update_data(description=message.message_id)
    data = await state.get_data()

    try:
        keyboard_endRep = InlineKeyboardMarkup().row(
            InlineKeyboardButton("да", callback_data=User_data_save.new(place=data["place"], description=data["description"])),
            InlineKeyboardButton("нет", callback_data="rep_no")
        )
    except:
        await message.answer("Трабл. Повторите завялене")
        await Rep.place.set()

    await message.answer(f"Проверте запрос!")
    await bot.forward_message(chat_id=message.chat.id, message_id=int(data['place']), from_chat_id=message.chat.id)
    await bot.forward_message(chat_id=message.chat.id, message_id=int(data['description']), from_chat_id=message.chat.id)
    await message.answer(f"Все верно?", reply_markup=keyboard_endRep)
    await state.finish()


@dp.callback_query_handler(User_data_save.filter())
async def Rep_yes(query: types.CallbackQuery, callback_data):
    """
    Выставление заявки report a problem из места проишествия и его описания
    :param query:
    :param callback_data:
    :return:
    """
    await bot.answer_callback_query(query.id)
    ansver = await s.Create_new_report(query.message, callback_data)
    if ansver:
        await query.message.edit_text("Заявка выставленна. Ожидайте решения проблемы", parse_mode="Markdown")
        await Menu(query.message)
    else:
        await query.message.edit_text("Произошла ошибка во время выставления заявки! Повторите позднее", parse_mode="Markdown")
        await Menu(query.message)

@dp.callback_query_handler(text="rep_no")
async def Rep_no(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await query.message.answer("Заявка отменена")
    await Menu(query.message)

#________________________________________________________________________________
#dont work
"""
при обновлении выполненной работы актором AHS заставить присылать запрос пользователю на коментарий к проделанной работе



@dp.callback_query_handler(text="kom")
async def Kom(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await query.message.answer("Напишите коментарий к проделанной работе")

#@dp.message_handler(state=Kom_user.st1)
async def Kom1(message: types.Message, state: FSMContext):
    await message.answer("Спасибо за ваш отзыв!")
    await state.finish()
    await Menu(message)
"""

"""
________________________________________________________________________________________________________________________________________________________________________________
                                                                                        mess watch at USER
________________________________________________________________________________________________________________________________________________________________________________
"""

class user_mess_watch(StatesGroup):
    mess = State()

@dp.callback_query_handler(text="mess")
async def User_mess_watch(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await query.message.answer("Напишите ваш запрос вахте (опишите его в одном сообщении):")
    await user_mess_watch.mess.set()

user_mess_watch_mess = CallbackData("mess_yes", "mess_id")

@dp.message_handler(state=user_mess_watch.mess)
async def User_mess_watch_mess(message: types.Message, state: FSMContext):
    await state.update_data(mess=message.message_id)
    data = await state.get_data()
    keyboard_end_mess = InlineKeyboardMarkup().row(
        InlineKeyboardButton("да",
                             callback_data=user_mess_watch_mess.new(mess_id=data["mess"])),
        InlineKeyboardButton("нет", callback_data="menu")
    )

    await message.answer(f"Проверте запрос!")
    await bot.forward_message(chat_id = message.chat.id, from_chat_id = message.chat.id, message_id = int(data['mess']))
    await message.answer(f"Все верно?", reply_markup=keyboard_end_mess)

    await state.finish()

@dp.callback_query_handler(user_mess_watch_mess.filter())
async def User_mess_watch_mess_yes(query: types.CallbackQuery, callback_data):
    await bot.answer_callback_query(query.id)

    await s.Create_new_request_watch(query.message, int(callback_data['mess_id']))
    await query.message.answer("Запрос отпрввлен")
    await Menu(query.message)

"""
________________________________________________________________________________________________________________________________________________________________________________
                                                                                        mess watch at USER
________________________________________________________________________________________________________________________________________________________________________________
"""

booking_ans = CallbackData("Boo_ans", "room", "time")

@dp.callback_query_handler(text="booking")
async def Booking(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)

    keyboard_Booking_room = InlineKeyboardMarkup().row(
        InlineKeyboardButton("Общая комната", callback_data=booking_ans.new(room="OK", time=0))
    ).row(
        InlineKeyboardButton("Спортзал", callback_data=booking_ans.new(room="SP", time=0))
    ).row(
        InlineKeyboardButton("Прачечная 1 этаж", callback_data=booking_ans.new(room="P1", time=0))
    ).row(
        InlineKeyboardButton("Прачечная 2 этаж", callback_data=booking_ans.new(room="P2", time=0))
    ).row(
        InlineKeyboardButton("В меню", callback_data="menu")
    )

    await query.message.answer("Выберите комнату:", reply_markup=keyboard_Booking_room )

@dp.callback_query_handler(booking_ans.filter())
async def Booking_ans(query: types.CallbackQuery, callback_data):
    await bot.answer_callback_query(query.id)
    if int(callback_data["time"]) == 0:
        keyboard_Booking_room = InlineKeyboardMarkup()
        ans = await s.Check_all_request_occupy(query.message)
        ans_time = []
        for i in ans:
            if i[2] == callback_data['room']:
                ans_time.append(i[1].hour)

        for i in range(8, 23, 1):
            if i in ans_time:
                pass
            else:
                keyboard_Booking_room.insert(
                    InlineKeyboardButton(f"{i}:00", callback_data=booking_ans.new(room= callback_data["room"], time=i))
                )

        keyboard_Booking_room.row(
            InlineKeyboardButton("В меню", callback_data="menu")
        )

        await query.message.answer("Выберите время:", reply_markup=keyboard_Booking_room)
    else:
        await s.New_booking(query.message, callback_data)
        await query.message.answer("Ждите подтверждения")

"""
________________________________________________________________________________________________________________________________________________________________________________
                                                                                        report a problem AHS
________________________________________________________________________________________________________________________________________________________________________________
"""

@dp.callback_query_handler(AHS_turn_trable.filter())
async def Turn_trabQ(query: types.CallbackQuery, callback_data):
    await bot.answer_callback_query(query.id)
    check = True
    if callback_data["trable"] == "end":
        check = await s.Сhange_status_report(query.message, callback_data)
        await query.message.answer("Статус проблемы изменен на решенную.\n Спасибо за работу!")

    if check:
        await Turn_trab(query.message, callback_data)

    else:
        await query.message.answer("Произошла неизвестная ошибка")
        await Menu(query.message)

async def Turn_trab(message: types.Message, callback_data):
    ansver = await s.Сhoose_a_problem(message, int(callback_data["namb_trable"]))
    if ansver == False:
        await message.answer("Проблемы закончились\nСпасибо за вашу работу")
        await Menu(message)
    else:
        keyboard_turn = InlineKeyboardMarkup().row(
            InlineKeyboardButton("Выйти",
                                 callback_data="menu"),
            InlineKeyboardButton("Решена", callback_data=AHS_turn_trable.new(namb_trable=ansver[0], trable="end")),
            InlineKeyboardButton("Пропустить", callback_data=AHS_turn_trable.new(namb_trable=ansver[0], trable="no"))
        )

        await message.answer(f"Проблема:")
        await bot.forward_message(chat_id=message.chat.id, message_id=int(ansver[1]), from_chat_id=int(ansver[4]))
        await bot.forward_message(chat_id=message.chat.id, message_id=int(ansver[2]), from_chat_id=int(ansver[4]))
        await message.answer(f"Статус: не решена", reply_markup=keyboard_turn)


"""
________________________________________________________________________________________________________________________________________________________________________________
                                                                                        Watch
________________________________________________________________________________________________________________________________________________________________________________
"""


@dp.callback_query_handler(text="status_swich")
async def Status_watch_svich(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    ans = await s.Status_work_watch_swich(query.message)
    if ans == True:
        await query.message.answer("Вы приступили к работе")
        await Menu(query.message)
    else:
        await query.message.answer("Ошибка! Обратитесь к администратору")
        await Menu(query.message)

class ver_unreg(StatesGroup):
    id = State()
    room = State()

@dp.callback_query_handler(text="vereficateon_unreg")
async def Vereficateon_unreg(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await query.message.answer("Введите код пользователя:")
    await ver_unreg.id.set()

@dp.message_handler(state=ver_unreg.id)
async def Vereficateon_unreg_id(message: types.Message, state: FSMContext):
    try:
        await state.update_data(id=message.text)
        text = int(message.text)
    except:
        await message.answer("Ошибка кода верефикации. Вы ввели не число")
        await state.finish()
        await Menu(message)
        return 0
    ans = await s.Check_user_privileges(message, text)
    if ans == "no_info":
        await message.answer("Ошибка кода верефикации. Неизвестный код пользователя")
        await state.finish()
        await Menu(message)
    elif ans == "user" or ans == "AHS" or ans == "watch":
        await message.answer("Ошибка кода верефикации. Код пользователя уже верефецирован")
        await state.finish()
        await Menu(message)
    else:
        await message.answer("Пользователь найден\n\nВведите номер его комнаты")
        await ver_unreg.next()


@dp.message_handler(state=ver_unreg.room)
async def Vereficateon_unreg_room(message: types.Message, state: FSMContext):
    if int(message.text) // 100 <= 9 and int(message.text) % 100 <= 26:
        await state.update_data(room=message.text)
        data = await state.get_data()
        ans = await s.Reg_user(message, int(data["id"]), int(data["room"]))
        if ans:
            await message.answer("Пользователь зарегестрирован и авторизован")
            await state.finish()
            await bot.send_message(chat_id=int(data["id"]),
                                   text=f"Теперь вы авторизованный пользователь\nПропешите /menu для перехода в меню бота")
            await Menu(message)
        else:
            await message.answer("Произошла неизвестная ошибка при регистрации пользователя. Обратитесь к администратору сети")
            await state.finish()
            await Menu(message)
    else:
        await message.answer("Неверно введен номер комнаты")
        await ver_unreg.room.set()



"""
________________________________________________________________________________________________________________________________________________________________________________
                                                                                        requests Watch 
________________________________________________________________________________________________________________________________________________________________________________
"""



@dp.callback_query_handler(text="requests")
async def Requestsq(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await Requests(query, {"page": -1, "action": "next", "type_r": 1, "user_id": 0})

class request_ansver(StatesGroup):
    ansver = State()
    type_r = State()
    id = State

request_reply_data = CallbackData("req_ans", "page", "action", "type_r", "user_id")
request_reply_booking = CallbackData("req_ans_book", "page", "action", "type_r", "user_id")

@dp.callback_query_handler(request_reply_data.filter())
async def Requests(query: types.CallbackQuery, callback_data):
    await bot.answer_callback_query(query.id)
    page = int(callback_data["page"])
    type_r = int(callback_data["type_r"])
    action = callback_data["action"]
    if action == "next":
        ans = await s.Request_for_requests(query.message, page, type_r)
        #print(callback_data, ans)
        if ans != []: # запросы закончились
            if type_r == 1: # Таблица Request_watch
                await query.message.answer("Вопрос:")
                await bot.forward_message(chat_id = query.message.chat.id, from_chat_id = int(ans[0][3]), message_id = int(ans[0][1]))

                keyboard_requests = InlineKeyboardMarkup().add(
                    InlineKeyboardButton("Ответить", callback_data=request_reply_data.new(page= ans[0][0],  action = "ans", type_r = 1, user_id = ans[0][3])),
                    InlineKeyboardButton("Пропустить", callback_data=request_reply_data.new(page= ans[0][0], action = "next", type_r = 1, user_id = 0))
                )

                await query.message.answer("Что делать?", reply_markup=keyboard_requests)
            else: #таблица Request_occupy
                keyboard_requests = InlineKeyboardMarkup().add(
                    InlineKeyboardButton("Подтвердить",
                                         callback_data=request_reply_booking.new(page=ans[0][0], action="yes", type_r=2,
                                                                              user_id=ans[0][4])),
                    InlineKeyboardButton("Отказать",
                                         callback_data=request_reply_booking.new(page=ans[0][0], action="no", type_r=2,
                                                                              user_id=ans[0][4]))
                )
                if ans[0][2] == "OK":
                    room = "Общая комната"
                elif ans[0][2] == "SP":
                    room = "Спортзал"
                elif ans[0][2] == "P1":
                    room = "Прачечная 1 этаж"
                elif ans[0][2] == "P2":
                    room = "Прачечная 2 этаж"
                await query.message.answer(f"Запрос бронировании комнаты:\n\n"
                                           f"Время: {ans[0][1].hour}:00\n"
                                           f"Комната: {room}\n"
                                           f"На: 1 час\n\n"
                                           f"Подтвердить?", reply_markup=keyboard_requests)
        else:
            if type_r == 1:
                await Requests(query, {"page": -1, "action": "next", "type_r": 2, "user_id": 0})
            else:
                await query.message.answer("Запросы закончились. Спасибо за работу")
                await Menu(query.message)
    else:
        await query.message.answer(f"Напишите данные цыфры (это важно!): {type_r} {page}")
        await request_ansver.type_r.set()

@dp.callback_query_handler(request_reply_booking.filter())
async def Request_reply_booking(query: types.CallbackQuery, callback_data):
    await bot.answer_callback_query(query.id)

    ans = await s.Update_request_reply_booking(query.message, callback_data)
    if callback_data["action"] == "yes" and ans != False:
        if ans[0][2] == "OK":
            room = "Общая комната"
        elif ans[0][2] == "SP":
            room = "Спортзал"
        elif ans[0][2] == "P1":
            room = "Прачечная 1 этаж"
        elif ans[0][2] == "P2":
            room = "Прачечная 2 этаж"
        else:
            room = None
        await bot.send_message(chat_id=callback_data["user_id"], text=f"Ваш запрос:\n\nвремя бронирования: {ans[0][1]}\nкомната: {room}\nна 1 час\n\nбыл подтвержден.\nПриходите и забирайте ключи.")
        await query.message.answer("Запрос подтвержден")
        await Requests(query, {"page": -1, "action": "next", "type_r": 2, "user_id": 0})
    elif callback_data["action"] == "no" and ans != False:
        if ans[0][2] == "OK":
            room = "Общая комната"
        elif ans[0][2] == "SP":
            room = "Спортзал"
        elif ans[0][2] == "P1":
            room = "Прачечная 1 этаж"
        elif ans[0][2] == "P2":
            room = "Прачечная 2 этаж"
        else:
            room = None
        await bot.send_message(chat_id=callback_data["user_id"], text=f"Ваш запрос:\n\n"
                                                                      f"время бронирования: {ans[0][1]}\n"
                                                                      f"комната: {room}\n"
                                                                      f"на 1 час\n\n"
                                                                      f"был отменен.\n")
        await query.message.answer("Запрос отвергнут")
        await Requests(query, {"page": -1, "action": "next", "type_r": 2, "user_id": 0})
    else:
        print("error")


@dp.message_handler(state=request_ansver.type_r)
async def Request_ansver_mess(message: types.Message, state: FSMContext):
    await state.update_data(type_r=(message.text.split(" "))[0])
    await state.update_data(id=(message.text.split(" "))[1])
    await message.answer("Теперь напишите ответ пользователю:")
    await request_ansver.ansver.set()

request_ans = CallbackData("req_ans_watch", "mess_id", "type_r", "id")

@dp.message_handler(state=request_ansver.ansver)
async def Request_ansver_mess(message: types.Message, state: FSMContext):
    await state.update_data(ansver=(message.message_id))
    ansver = await state.get_data()
    await state.finish()
    await message.answer("Проверьте ответ")
    await bot.forward_message(chat_id=message.chat.id, from_chat_id=message.chat.id, message_id=ansver["ansver"])

    keyboard_ans_request = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Да", callback_data=request_ans.new(mess_id = ansver["ansver"], type_r=ansver["type_r"], id=ansver["id"])),
        InlineKeyboardButton("Нет", callback_data="requests")
    )

    await message.answer("Все верно?", reply_markup= keyboard_ans_request)


@dp.callback_query_handler(request_ans.filter())
async def Requests_ansver_mess_ans_user(query: types.CallbackQuery, callback_data):
    await bot.answer_callback_query(query.id)
    ansver = int(callback_data["mess_id"])
    type_r = int(callback_data["type_r"])
    id = int(callback_data["id"])

    if type_r == 1:
        ans = await s.Check_user_id_ans_request_write(query.message, id)
    else:
        ans = await s.Check_user_id_ans_Request_occupy(query.message, id)
    await bot.send_message(chat_id=ans[0], text="На ваш запрос:")

    print(ans[0], query.message.chat.id, int(ans[1]))

    await bot.forward_message(chat_id=ans[0], from_chat_id=ans[0], message_id=int(ans[1]))
    await bot.send_message(chat_id=ans[0], text="поступил ответ:")
    await bot.forward_message(chat_id=ans[0], from_chat_id=query.message.chat.id, message_id=ansver)

    #обновить базу данных
    await s.Update_request(query.message, type_r, id, ansver)

    await query.message.answer("Ответ отправлен")
    await Requests(query, {"page": -1, "action": "next", "type_r": type_r, "user_id": 0})



#______________________________________________________________________________________________________

keyboard_Board = InlineKeyboardMarkup().row(
    InlineKeyboardButton("Ищу холодильник", callback_data="111")
).row(
    InlineKeyboardButton("Отдам чайник", callback_data="112")
).row(
    InlineKeyboardButton("Нашел футболку!", callback_data="bt2_futbolka")
).row(
    InlineKeyboardButton("Создать объявление", callback_data="new_add"),
    InlineKeyboardButton("В меню", callback_data="next2")
)


@dp.callback_query_handler(text="bt2")
async def Bt2(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await query.message.answer("Доска объявлений\n\nЗдесь можно найти то, что вы ищите или оставить свои объявления", reply_markup=keyboard_Board)

keyboard_end =InlineKeyboardMarkup().row(
    InlineKeyboardButton("В меню", callback_data="next2")
)

@dp.callback_query_handler(text="bt2_futbolka")
async def Bt2(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await query.message.answer("Нашел футболку!\n\nЕсли хотите ее вернуть пишите @_pt1chka_ ")
    photo = open('D:/code/тсарые боты/TimesKursovaiRabota/Futbolka.jpg', 'rb')
    await bot.send_photo(query.message.chat.id, photo=photo)
    photo.close()
    await query.message.answer("Действия", reply_markup=keyboard_end)

#______________________________________________________________________________________________________

keyboard_room = InlineKeyboardMarkup().row(
    InlineKeyboardButton("Общая комната", callback_data="ob_room")
).row(
    InlineKeyboardButton("Спортзал", callback_data="sport_room")
).row(
    InlineKeyboardButton("Прачечная 1 этаж", callback_data="pr1_room")
).row(
    InlineKeyboardButton("Прачечная 2 этаж", callback_data="pr2_room")
).row(
    InlineKeyboardButton("В меню", callback_data="next2")
)

@dp.callback_query_handler(text="bt3")
async def Bt3(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await query.message.answer("Выберите комнату", reply_markup=keyboard_room)

keyboard_room_pt1 = InlineKeyboardMarkup().row(
    InlineKeyboardButton("Занять время", callback_data="pr1_room_zan")
)

@dp.callback_query_handler(text="pr1_room")
async def Pr1_room(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await query.message.answer("Расписание 'Прачечная 1 этаж'\n\n"
                               "8:00-9:00 - занято\n"
                               "9:00-10:00 - занято\n"
                               "10:00-11:00 - занято\n"
                               "11:00-12:00 - свободно\n"
                               "12:00-13:00 - свободно\n"
                               "13:00-14:00 - занято\n"
                               "14:00-15:00 - занято\n"
                               "15:00-16:00 - занято\n"
                               "16:00-17:00 - занято\n"
                               "17:00-18:00 - свободно\n"
                               "18:00-19:00 - занято\n"
                               "19:00-20:00 - свободно\n", reply_markup=keyboard_room_pt1)

class Pr1_room_zan_vr(StatesGroup):
    st1 = State()

@dp.callback_query_handler(text="pr1_room_zan")
async def Pr1_room_zan(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await query.message.answer("Введите время которое хотите занять")
    await Pr1_room_zan_vr.st1.set()

@dp.message_handler(state=Pr1_room_zan_vr.st1)
async def Pr1_room_zan_vr_s(message: types.Message, state: FSMContext):
    text = message.text
    await state.finish()
    await message.answer("Подождите одбрения заявки")
    await message.answer(f"Заявка одобренна!\n\nВаше время: {text}\nПриходите и забирайте ключь в забронированное время", reply_markup=keyboard_end)


#______________________________________________________________________________________________________

class bt4_mess(StatesGroup):
    st1 = State()

@dp.callback_query_handler(text="bt4")
async def Bt4(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await bt4_mess.st1.set()
    await query.message.answer("Напишите ваше сообщение вахте")

@dp.message_handler(state=bt4_mess.st1)
async def Bt4_mess(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Ваше сообщение пришло и будет обработано в ближайшее время", reply_markup=keyboard_end)

#______________________________________________________________________________________________________



#______________________________________________________________________________________________________
#______________________________________________________________________________________________________
"""

status = "Не работаю"

@dp.message_handler(commands=['start_watch'])
async def Start_Bot(message: types.Message):
    await Menu_watch(message)



@dp.callback_query_handler(text="status_svich")
async def Bt5(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    global status
    if status == "Не работаю":
        status = "Работаю"
    else:
        status = "Не работаю"
    await Menu_watch(query.message)

@dp.callback_query_handler(text="menu_watch")
async def Menu_callback(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await Menu_watch(query.message)

async def Menu_watch(message: types.Message):
    global status
    if status == "Не работаю":
        button_status = InlineKeyboardButton("Начать работу", callback_data="status_svich")
    else:
        button_status = InlineKeyboardButton("Закончить работу", callback_data="status_svich")
    keyboard_menu_watch = InlineKeyboardMarkup().row(
        button_status,
        InlineKeyboardButton("Верификация", callback_data="btw1")
    ).row(
        InlineKeyboardButton("Запросы", callback_data="btw2"),
        InlineKeyboardButton("Доска потеряшек", callback_data="btw3")
    ).row(
        InlineKeyboardButton("Написать объявление", callback_data="btw4")
    )
    await message.answer("Главное меню\n\n"
                         f"Cтатус: <b>{status}</b>",reply_markup=keyboard_menu_watch, parse_mode = types.ParseMode.HTML)

# ______________________________________________________________________________________________________

class btw1_mess(StatesGroup):
    st1 = State()

@dp.callback_query_handler(text="btw1")
async def Btw1(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await btw1_mess.st1.set()
    await query.message.answer("Верефикация пользователя\n\nВведите индивидуальный индификатор")

async def Btw1_rel(message: types.Message):
    await btw1_mess.st1.set()
    await message.answer("Верефикация пользователя\n\nВведите индивидуальный индификатор")

@dp.message_handler(state=btw1_mess.st1)
async def Btw1_mess(message: types.Message, state: FSMContext):
    if message.text == "065346" or message.text == "#065346":
        await message.answer("Пользователь индифицирован")
        await state.finish()
        await Menu_watch(message)
    else:
        await message.answer("Пользователь не индифицирован попробуйте повторить")
        await state.finish()
        await Btw1_rel(message)

# ______________________________________________________________________________________________________

zan1 = InlineKeyboardButton("Занять комнату! 'Прачечная 1 этаж' на время '12:00-13:00'", callback_data="zan_1")
zan2 = InlineKeyboardButton("Вызов! 'в 605 комнате сильно шумят и мешают людям спать'", callback_data="zan_2")
MM = InlineKeyboardButton("В меню", callback_data="menu_watch")

trabls = {"zan1": True, "zan2": True}

@dp.callback_query_handler(text="btw2")
async def Btw2(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await Btw2_menu(query.message)

async def Btw2_menu(message: types.Message):

    global trabls

    keyboard_zapros = InlineKeyboardMarkup()
    if trabls["zan1"]:
        keyboard_zapros.row(zan1)
    if trabls["zan2"]:
        keyboard_zapros.row(zan2)
    keyboard_zapros.row(MM)
    await message.answer("Запросы:", reply_markup=keyboard_zapros)

@dp.callback_query_handler(text="zan_1")
async def Zan_1(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)

    keyboard_zan1_ansver = InlineKeyboardMarkup().row(
        InlineKeyboardButton("Да", callback_data="yes_zan1"),
        InlineKeyboardButton("Нет", callback_data="no_zan1")
    )
    await query.message.answer("Занять комнату!\n\n"
                               "'Прачечная 1 этаж' на время '12:00-13:00'", reply_markup=keyboard_zan1_ansver)

@dp.callback_query_handler(text="yes_zan1")
async def Yes_zan1(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    global trabls
    trabls["zan1"] = False
    await query.message.answer("Запрос одобрен")
    await Btw2_menu(query.message)

@dp.callback_query_handler(text="zan_2")
async def Zan_2(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)

    keyboard_waorkend = InlineKeyboardMarkup().row(InlineKeyboardButton("Выполненно",callback_data="end_zan2"))

    await query.message.answer("Вызов!\n\n'в 605 комнате сильно шумят и мешают людям спать'", reply_markup=keyboard_waorkend)

@dp.callback_query_handler(text="end_zan2")
async def End_zan2(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    global trabls
    trabls["zan2"] = False
    await Btw2_menu(query.message)
"""

class post(StatesGroup):
    st1 = State()


@dp.callback_query_handler(text="btw4")
async def Btw4(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await query.message.answer("Напишите пост")
    await post.st1.set()

keyboard_post = InlineKeyboardMarkup().row(
    InlineKeyboardButton("Да", callback_data="yes_post"),
    InlineKeyboardButton("Нет", callback_data="yes_post")
)

@dp.message_handler(state=post.st1)
async def Post(message: types.Message, state: FSMContext):
    await message.answer("Ваш пост:")
    await message.answer(message.text)
    await state.finish()
    await message.answer("Публиковать пост?", reply_markup=keyboard_post)

@dp.callback_query_handler(text="yes_post")
async def Yes_post(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await query.message.answer("Пост опубликован")
    await Menu(query.message)

# ______________________________________________________________________________________________________


keyboard_Board_watch = InlineKeyboardMarkup().row(
    InlineKeyboardButton("Ищу холодильник", callback_data="111")
).row(
    InlineKeyboardButton("Отдам чайник", callback_data="112")
)
futbolka = True

@dp.callback_query_handler(text="btw3")
async def Btw3(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    global futbolka
    if futbolka:
        keyboard_Board_watch.row(
            InlineKeyboardButton("Нашел футболку!", callback_data="bt2_futbolka_watch")
        ).row(
            InlineKeyboardButton("Создать объявление", callback_data="new_add_watch"),
            InlineKeyboardButton("В меню", callback_data="menu_watch")
        )
    else:
        keyboard_Board_watch.row(
            InlineKeyboardButton("Создать объявление", callback_data="new_add_watch"),
            InlineKeyboardButton("В меню", callback_data="menu")
        )
    await query.message.answer("Доска объявлений\n\nЗдесь можно найти то, что вы ищите или оставить свои объявления", reply_markup=keyboard_Board_watch)

keyboard_end_watch =InlineKeyboardMarkup().row(
    InlineKeyboardButton("В меню", callback_data = "menu"),
    InlineKeyboardButton("Удалить запись", callback_data = "del_watch")
)

@dp.callback_query_handler(text="bt2_futbolka_watch")
async def Btw3_watch(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await query.message.answer("Нашел футболку!\n\nЕсли хотите ее вернуть пишите @_pt1chka_ ")
    photo = open('D:/code/тсарые боты/TimesKursovaiRabota/Futbolka.jpg', 'rb')
    await bot.send_photo(query.message.chat.id, photo=photo)
    photo.close()
    await query.message.answer("Действия", reply_markup=keyboard_end_watch)

@dp.callback_query_handler(text="del_watch")
async def Del_watch(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)

    global futbolka
    futbolka = False

    await query.message.answer("Запись удалена")
    await Menu_watch(query.message)

# ______________________________________________________________________________________________________

#старт бота
def main():

    executor.start_polling(dispatcher = dp, skip_updates = True)

if __name__ == "__main__":
	main()