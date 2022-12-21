import random
import mysql.connector
from mysql.connector import Error
from datetime import date
import uuid

dbname="hotel_chatbot"
room_type=["Single", "Deluxe"]
room_price=[50,70]
room_unit=[5,3]

def execute(query):
    results=True
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="password",
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(query)
            for x in cursor:
                print(x)
    except Error as e:
        print("Error while connecting to MySQL", e)
        results=False
    finally:
        if connection.is_connected():
            connection.commit()
            cursor.close()
            connection.close()
            return results

def create_room_table(dbname):
    return execute("""
    CREATE TABLE {}.room (
        room_id int NOT NULL AUTO_INCREMENT,
        room_type varchar(31) NOT NULL, 
        price float(8) NOT NULL, 
        num float(8) NOT NULL,
        PRIMARY KEY(room_id))
    """.format(dbname))

def add_room(dbname, room_type,price,num):
    return execute("""
    INSERT INTO {}.room VALUES (DEFAULT, '{}', {}, {})
    """.format(dbname,room_type, price, num)
    )

def create_hotel_table(dbname):
    return execute("""
    CREATE TABLE {}.hotel (
        room_id int NOT NULL,
        date DATE NOT NULL,
        num_available int NOT NULL
        )
    """.format(dbname))

def add_availability(dbname):
    for day in range(1,31):
        for i in range(len(room_type)):
            execute("""
            INSERT INTO {}.hotel VALUES ({}, CURDATE() + INTERVAL {} DAY, {}) 
            """.format(dbname,i+1, day, room_unit[i])
            )

def create_boooking_table(dbname):
    return execute("""
    CREATE TABLE {}.booking (
        id varchar(255) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        room_id int NOT NULL,
        price float(8) NOT NULL
        )
    """.format(dbname))

#BOOKING: id, start_date, end_date, room_id, price
#HOTEL: date, room_id, num_available
#ROOM: room_id, room_type, price, num
def create_db():
    execute("CREATE DATABASE {}".format(dbname))
    if create_room_table(dbname):
        for i in range(len(room_type)):
            add_room(dbname, room_type[i],room_price[i],room_unit[i])
    if create_hotel_table(dbname):
        add_availability(dbname)
    create_boooking_table(dbname)
    return

def auto_update_db():
    return

def get_availability(dbname,start_date,end_date,room_type):
    results=0
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="password",
            database=dbname
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("""
            SELECT MIN(num_available) FROM hotel
            LEFT JOIN room
            ON hotel.room_id=room.room_id
            WHERE date BETWEEN '{}' AND '{}'
            AND room_type='{}'
            GROUP BY room_type
            """.format(start_date,end_date,room_type))
            for x in cursor:
                print(x)
                results=x[0]
    except Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if connection.is_connected():
            connection.commit()
            cursor.close()
            connection.close()
            return results

def make_booking(dbname,start_date,end_date,room_type):
    if not get_availability(dbname,start_date,end_date,room_type):
        print("Room full")
        return None
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="password",
            database=dbname
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("""
            SELECT room_id,price FROM room WHERE room_type='{}'
            """.format(room_type))
            for x in cursor:
                room_id=x[0]
                price=x[1]
    except Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if connection.is_connected():
            connection.commit()
            cursor.close()
            connection.close()
    end=date(int(end_date[0:4]),int(end_date[5:7]),int(end_date[8:]))
    start=date(int(start_date[0:4]),int(start_date[5:7]),int(start_date[8:]))
    days=(end-start).days
    price*=days
    id=uuid.uuid4()
    execute("""
    INSERT INTO {}.booking VALUES(
        '{}','{}','{}',{},{}
    )""".format(dbname,id,start_date,end_date,room_id,price))
    print(id)
    execute("""
    UPDATE {}.hotel SET num_available=num_available-1 WHERE date>='{}' AND date<'{}' AND room_id={}
    """.format(dbname,start_date,end_date,room_id))
    return id
    #Provide suggestion such as breakfast, spa, room service

def get_booking_details(dbname, id):
    start_date,end_date,room_id,room_type,price=None,None,None,None,None
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="password",
            database=dbname
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("""
            SELECT * FROM booking LEFT JOIN room
            ON booking.room_id=room.room_id WHERE id='{}'
            """.format(id))
            for x in cursor:
                print(x)
                start_date=x[1]
                end_date=x[2]
                room_id=x[3]
                room_type=x[6]
                price=x[4]
    except Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if connection.is_connected():
            connection.commit()
            cursor.close()
            connection.close()
    return start_date,end_date,room_id,room_type,price

def cancel_booking(dbname, id):
    start_date,end_date,room_id,room_type,price=get_booking_details(dbname,id)
    if start_date:
        execute("""
    DELETE FROM {}.booking WHERE id='{}'
    """.format(dbname,id))
        execute("""
        UPDATE {}.hotel SET num_available=num_available+1 WHERE date>='{}' AND date<'{}' AND room_id={}
        """.format(dbname,start_date,end_date,room_id))
        return True
    return False

def get_room_types(dbname):
    room_types=[]
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="password",
            database=dbname
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("""
            SELECT * FROM room
            """)
            for x in cursor:
                room_types.append(x[1])
    except Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if connection.is_connected():
            connection.commit()
            cursor.close()
            connection.close()
    return room_types

def get_facilities():
    return ["Spa","Pool"]

def get_nearby_restaurants():
    return random.choice(["Turkish House Restaurant","Bait Al Karam Restaurant","Al Ziyara Restaurant","Bin Ateeq","Begum's"])

def get_nearby_attractions():
    return random.choice(["Sultan Qaboos Grand Mosque","Royal Opera House Museum","Qurum Beach","Mutrah Souq","Mutrah Corniche"])

def get_hotel_contact():
    return "+968 9406 0891"

if __name__=="__main__":
    create_db()
    execute("""SELECT * FROM {}.hotel""".format(dbname))
    print(get_availability(dbname,"2022-12-24","2022-12-26","Single"))
    make_booking(dbname,"2022-12-19","2022-12-22","Single")
    #make_booking(dbname,"2022-12-22","2022-12-23","Single")
    print(get_booking_details(dbname,input()))
    execute("""DROP DATABASE {}""".format(dbname))