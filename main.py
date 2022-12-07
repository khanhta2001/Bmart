import datetime

import mysql.connector
from mysql.connector import errorcode


def reorder(store):
    try:
        cnx = mysql.connector.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')
        cursor = cnx.cursor()
        query = ("SELECT * FROM store WHERE store_id = %s")
        params = (store,)
        cursor.execute(query, params)
        if cursor.rowcount == 0:
            print("There is no such store")
            return
        else:
            try:
                order_request = ("SELECT * FROM order_request WHERE store_id = %s")
                cursor.execute(order_request, params)
                store_order_request = cursor.fetchall()
                store_inventory = ("SELECT * FROM inventory_space WHERE store_id = %s")
                cursor.execute(store_inventory, params)
                store = cursor.fetchone()
                item_price = ("SELECT * FROM price WHERE product_id = %s")
                cursor.execute(item_price, (store['product_id'],))
                price = cursor.fetchone()
                vendor = price['vendor_id']
                product_price = price['sell_price']
                current_stock = store['current_stock']
                max_stock = store['maximum_space']
                if current_stock == max_stock:
                    print("There is no need to reorder")
                    return
                else:
                    if store_order_request is None:
                        print("Reorder is needed")
                    elif store_order_request is not None:
                        total_amount = 0
                        for row in store_order_request:
                            total_amount += row['amount_requested']
                        if total_amount + current_stock <= max_stock:
                            print("Reorder is needed")
                            reorder_amount = max_stock - current_stock - total_amount
                            print("Reorder amount is: ", reorder_amount)
                            reorder_query = (
                                "INSERT INTO order_request (vendor_id, amount_requested, order_time, total_cost, order_status,seen_or_not) VALUES (%s, %s, %s, %s, %s, %s)")
                            params = (
                                vendor, reorder_amount, datetime.datetime.now(), product_price * reorder_amount, False,
                                False)
                            cursor.execute(reorder_query, params)
                            return
                        else:
                            print("Order requests are already made")
                            return
                    return
            except:
                print("Invalid reorder item!")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        cnx.close()


def vendor_shipment():
    try:
        cnx = mysql.connector.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        cnx.close()


def stockInventory():
    try:
        cnx = mysql.connector.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        cnx.close()


def OnlineOrder():
    try:
        cnx = mysql.connector.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        cnx.close()


reorder(1)
