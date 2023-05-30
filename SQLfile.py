from psycopg2 import OperationalError
import psycopg2
import json
import datetime

from aiogram import types
from settings import connection

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from settings import bot


async def Check_user_privileges(message: types.Message, id = 0):
    """
    функция выявления роли актора который использует этого бота
    :param message:
    :return: unreg, user, watch, AHS, no_info
    """
    if id ==0:
        insert_query = (f'SELECT id, name, token FROM public."Unregister_users" where id = {message.chat.id};')
        cursor = connection.cursor()
        cursor.execute(insert_query)
        result = cursor.fetchall()
        if result == []:
            insert_query = (f'SELECT id, name, token FROM public."Users" where id = {message.chat.id};')
            cursor = connection.cursor()
            cursor.execute(insert_query)
            result = cursor.fetchall()
            if result == []:
                insert_query = (f'SELECT id, name, token FROM public."Watch" where id = {message.chat.id};')
                cursor = connection.cursor()
                cursor.execute(insert_query)
                result = cursor.fetchall()
                if result == []:
                    insert_query = (f'SELECT id, name, token FROM public."AHS" where id = {message.chat.id};')
                    cursor = connection.cursor()
                    cursor.execute(insert_query)
                    result = cursor.fetchall()
                    if result == []:
                        return "no_info"
                    else:
                        return "AHS"
                else:
                    return "watch"
            else:
                return "user"
        else:
            return "unreg"
    else:
        insert_query = (f'SELECT id, name, token FROM public."Unregister_users" where id = {id};')
        cursor = connection.cursor()
        cursor.execute(insert_query)
        result = cursor.fetchall()
        if result == []:
            insert_query = (f'SELECT id, name, token FROM public."Users" where id = {id};')
            cursor = connection.cursor()
            cursor.execute(insert_query)
            result = cursor.fetchall()
            if result == []:
                insert_query = (f'SELECT id, name, token FROM public."Watch" where id = {id};')
                cursor = connection.cursor()
                cursor.execute(insert_query)
                result = cursor.fetchall()
                if result == []:
                    insert_query = (f'SELECT id, name, token FROM public."AHS" where id = {id};')
                    cursor = connection.cursor()
                    cursor.execute(insert_query)
                    result = cursor.fetchall()
                    if result == []:
                        return "no_info"
                    else:
                        return "AHS"
                else:
                    return "watch"
            else:
                return "user"
        else:
            return "unreg"


async def Check_work_status_watch(message: types.Message):
    """
    функция выявления статуса работы
    :param message:
    :return: возвращает статус нахождения на работе. 0 - не на работе, 1 - на рабочем месте
    """
    insert_query = (f'SELECT status FROM public."Watch" where id = {message.chat.id};')
    cursor = connection.cursor()
    try:
        cursor.execute(insert_query)
        result = cursor.fetchall()
        return result[0][0]
    except:
        return -1


async def New_unregister_user(message: types.Message, connection):
    """
    функция выдавания статуса unregister_user для новых пользователей
    :param message:
    :param connection:
    :return: True - Все прошло хорошо, False - пользователь уже зарегестрирован или уже начинал аундификацию
    """

    check = await Check_user_privileges(message)

    if check == "user" or check == "watch" or check == "AHS":
        await message.answer(f"Вы уже авторизированный пользователь.")
        return False
    elif check == "unreg":
        await message.answer(f"Вы уже начали аундификацию.\nПройдите на вахту и назовите свой инивидуальный номер: {message.chat.id}")
        return False
    else:
        insert_query = (f'INSERT INTO public."Unregister_users" ("id", "name", "token") VALUES (%s, %s, %s)')
        cursor = connection.cursor()
        try:
            cursor.execute(insert_query, [message.chat.id, message.chat.first_name + " " + message.chat.last_name, message.chat.username])
            return True
        except:
            try:
                cursor.execute(insert_query, [message.chat.id, None, message.chat.username])
                return True
            except: #пользователь уже находился в Unregister_users
                pass


async def Reg_user(message: types.Message, userid, room = 0):
    """
    Функция перевода пользователя из unregister_user в Regular_user
    :param message:
    :param connection:
    :param userid:
    :param room:
    :return: True - при успехе, False - при провале
    """
    insert_query1 = (f'SELECT id, name, token FROM public."Unregister_users" where id = {userid};')
    insert_query2 = (f'DELETE FROM public."Unregister_users" where id = {userid};')
    insert_query3 = (f'INSERT INTO public."Users" ("id", "name", "token", "room", "status") VALUES (%s, %s, %s, %s, %s);')
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(insert_query1)
        result = cursor.fetchall()
        result = result[0]
    except:
        return False
    try:
        cursor = connection.cursor()
        cursor.execute(insert_query2)
        cursor = connection.cursor()
        cursor.execute(insert_query3,[result[0], result[1], result[2], 0, 0])
        return True
    except OperationalError as e:
        print(f"The error '{e}' occurred")
        return False


async def Create_new_report(message: types.Message, callback_data):
    """
    создание новога запроса атрибута report a problem
    :param message:
    :param callback_data:
    :return:
    """
    insert_query = (f'INSERT INTO public."Report" ("place", "type_of_problem", "status", "evaluation", "user_id") VALUES (%s, %s, %s, %s, %s);')
    cursor = connection.cursor()
    try:
        cursor.execute(insert_query, [callback_data["place"], callback_data["description"], 0, None, message.chat.id])
        return True
    except OperationalError as e:
        print(f"The error '{e}' occurred")
        return False


async def Status_work_watch_swich(message: types.Message):
    insert_query = (f'SELECT status FROM public."Watch" where id = {message.chat.id};')
    cursor = connection.cursor()
    try:
        cursor.execute(insert_query)
        result = cursor.fetchall()
        result = result[0][0]
    except:
        return False
    if result == 0:
        del_query = f'''UPDATE "Watch" set "status"= 1 where "id"={message.chat.id};'''
    else:
        del_query = f'''UPDATE "Watch" set "status"= 0 where "id"={message.chat.id};'''
    try:
        cursor = connection.cursor()
        cursor.execute(del_query)
        return True
    except:
        return False

async def Сhoose_a_problem(message: types.Message, namb_trable):
    if namb_trable == -1:
        insert_query = (f'SELECT id, place, type_of_problem, status, user_id FROM public."Report" where id = (select min("id") from public."Report" where status = 0);')
        cursor = connection.cursor()
        try:
            cursor.execute(insert_query)
            result = cursor.fetchall()
            result = result[0]
            return result
        except:
            return False

    else:
        insert_query = (f'SELECT id, place, type_of_problem, status, user_id FROM public."Report" where id = (select min("id") from public."Report" where status = 0 and id > {namb_trable});')
        cursor = connection.cursor()
        try:
            cursor.execute(insert_query)
            result = cursor.fetchall()
            result = result[0]
            return result
        except:
            return False


async def Сhange_status_report(message: types.Message, collback_data):
    """
    Изменение статуса запроса и оповещение создателя запросса
    :param message:
    :param collback_data:
    :return:
    """
    update_query = f'''UPDATE "Report" set "status"= 1, "do"={message.chat.id} where "id"={int(collback_data["namb_trable"])};'''
    cursor = connection.cursor()
    try:
        cursor.execute(update_query)
    except:
        return False

    insert_query = (f'SELECT place, type_of_problem, user_id FROM public."Report" where id = {int(collback_data["namb_trable"])};')
    cursor = connection.cursor()
    try:
        cursor.execute(insert_query)
        result = cursor.fetchall()
        await bot.send_message(chat_id = int(result[0][2]), text=f"Ваша проблема:")
        await bot.forward_message(chat_id = int(result[0][2]), from_chat_id = int(result[0][2]), message_id = int(result[0][0]))
        await bot.forward_message(chat_id=int(result[0][2]), from_chat_id=int(result[0][2]), message_id=int(result[0][1]))
        keyboard_menu = InlineKeyboardMarkup().add(InlineKeyboardButton("В меню", callback_data="menu"))
        await bot.send_message(chat_id=int(result[0][2]), text=f"В данный момент является завершенной.Проверьте исполнение работы!",
                               reply_markup = keyboard_menu)
        return True
    except:
        return False


async def Create_new_request_watch(message: types.Message, mess_id):
    insert_query = (
        f'INSERT INTO public."Request_write" ("user_mess_id", "admin_mess_id", "user_id", "admin_id") VALUES (%s, %s, %s, %s);')
    cursor = connection.cursor()
    try:
        cursor.execute(insert_query, [mess_id, None, message.chat.id, None])
        """
        Отправить сообщение для всех работающих Watch
        """
        return True
    except OperationalError as e:
        print(f"The error '{e}' occurred")
        return False



async def Request_for_requests(message: types.Message, page, type_r):
    if type_r == 1:
        insert_query = (f'SELECT * FROM public."Request_write" where id = (select min(id) from public."Request_write" where admin_id is null and id > {page});')
        cursor = connection.cursor()
        try:
            cursor.execute(insert_query)
            result = cursor.fetchall()
        except:
            return False
        return result
    else:
        insert_query = (f'SELECT * FROM public."Request_occupy" where id = (select min(id) from public."Request_occupy" where status=0 and id > {page});')
        cursor = connection.cursor()
        try:
            cursor.execute(insert_query)
            result = cursor.fetchall()
        except:
            return False
        return result

async def Update_request(message: types.Message, type_r, id, mess):
    if type_r == 1:
        update_query = f'''UPDATE "Request_write" set "admin_mess_id"= {mess}, "admin_id"= {message.chat.id} where "id"={id};'''
        cursor = connection.cursor()
        try:
            cursor.execute(update_query)
            return True
        except:
            return False
    else:
        pass
        """
        update_query = f'''UPDATE "Request_write" set "admin_mess_id"= {mess}, "admin_id"= {message.chat.id} where "id"={id};'''
        cursor = connection.cursor()
        try:
            cursor.execute(update_query)
            return True
        except:
            return False
        """

async def Check_user_id_ans_request_write(message: types.Message, id):
    insert_query = (f'SELECT user_id, user_mess_id FROM public."Request_write" where id = {id};')
    cursor = connection.cursor()
    try:
        cursor.execute(insert_query)
        result = cursor.fetchall()
    except:
        return False
    return result[0]


async def Check_user_id_ans_Request_occupy(message: types.Message, id):
    insert_query = (f'SELECT user_id FROM public."Request_occupy" where id = {id};')
    cursor = connection.cursor()
    try:
        cursor.execute(insert_query)
        result = cursor.fetchall()
    except:
        return False
    return result[0]


async def Check_all_request_occupy(message: types.Message):
    insert_query = (f'select * from public."Request_occupy" where booking_time::date = (select CURRENT_DATE);')
    cursor = connection.cursor()
    try:
        cursor.execute(insert_query)
        result = cursor.fetchall()
    except:
        return False
    return result


async def New_booking(message: types.Message, callback_data):
    insert_query = (
        f'INSERT INTO public."Request_occupy" ("booking_time", "booking_room", "status", "user_id", "booking_time_end") VALUES (%s, %s, %s, %s, %s);')
    cursor = connection.cursor()
    try:
        cursor.execute(insert_query, [
            datetime.datetime(
                datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day,
                int(callback_data["time"])
            ),
            callback_data["room"],
            0,
            message.chat.id,
            1
        ])
        """
        Отправить сообщение для всех работающих Watch
        """
        return True
    except OperationalError as e:
        print(f"The error '{e}' occurred")
        return False

async def Update_request_reply_booking(message: types.Message, callback_data):
    select_query = (f'select * from public."Request_occupy" where id = {callback_data["page"]};')
    cursor = connection.cursor()
    try:
        cursor.execute(select_query)
        result = cursor.fetchall()
    except:
        return False
    if callback_data["action"] == "yes":
        update_query = f'''UPDATE "Request_occupy" set "status"= 1 where "id"= {callback_data["page"]};'''
        cursor = connection.cursor()
        try:
            cursor.execute(update_query)
            return result
        except:
            return False
    else:
        del_query = f'''DELETE FROM public."Request_occupy" WHERE id = {callback_data["page"]};;'''
        cursor = connection.cursor()
        try:
            cursor.execute(del_query)
            return result
        except:
            return False