import datetime

import mysql.connector
from mysql.connector import errorcode


def reorder(store):
    try:
        cnx = mysql.connector.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')
        cursor = cnx.cursor(buffered=True)
        query = "SELECT * FROM store WHERE store_id = %s"
        params = (store,)
        cursor.execute(query, params)
        store_inventory = "SELECT * FROM inventory_space WHERE store_id = %s"
        cursor.execute(store_inventory, (store,))
        store_items = cursor.fetchone()
        item_price = "SELECT * FROM price WHERE product_id = %s"
        # This currently orders the same item over and over again
        # should probably add loop to add several different items 
        cursor.execute(item_price, (store_items[0],))
        price = cursor.fetchone()
        vendor = price[0]
        product_price = price[3]
        current_stock = store_items[3]
        max_stock = store_items[2]
        if current_stock == max_stock:
            print("There is no need to reorder")
            return
        else:
            try:
                # Add a check to see if the request id is equivalentt to the request we are working 
                order_request = "SELECT * FROM order_request"
                cursor.execute(order_request)
                store_order_request = cursor.fetchall()
                total_amount = 0
                if store_order_request is None:
                    print("There is no previous order request.")
                elif store_order_request is not None:
                    for row in store_order_request:
                        total_amount += row[4]
                if total_amount + current_stock < max_stock:
                    print("Reorder is needed")
                    reorder_amount = max_stock - current_stock - total_amount
                    print("Reorder amount is:", reorder_amount)
                    reorder_query = (
                        "INSERT INTO order_request (vendor_id, store_id, amount_requested, order_time, "
                        "total_cost, order_status,seen_or_not) VALUES (%s,%s, %s, %s, %s, %s, %s)")
                    params = (vendor, store, reorder_amount, datetime.datetime.now(), product_price * reorder_amount, 0,0)
                    cursor.execute(reorder_query, params)
                    cnx.commit()
                    return
                else:
                    print("Order requests are already made")
                    return
            except:
                cnx.rollback()
                print("Something went wrong: {}")
    except mysql.connector.Error as err:
        print("Something went wrong: {}")
        cnx.close()


def vendor_shipment(store, delivery_time, reorder_list, shipment_items):
    try:
        cnx = mysql.connector.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')
        cursor = cnx.cursor(buffered=True)
    # The shipments must be inserted into the database
        # Print a list of all the products in the shipment
        all_items = ' '
        for item in shipment_items:
             # use specific column names when selecting, * is baddddd 
             # add a name field to product table
            get_product = "SELECT name FROM product WHERE product_id = %s"
            params = (item,)
            cursor.execute(get_product, params)
            product_name = cursor.fetchone()
            all_items  += product_name[0]
            print(all_items)

            # grab the number of each product

        # A list of completed orders
        print(reorder_list)

        # Remaining reorder requests for this store particularly
        orders_rem = "SELECT COUNT(store_id) FROM order_request WHERE store_id = %s AND order_status = 1"
        params5 = (store,)
        cursor.execute(orders_rem, params5)
        order_request = cursor.fetchone()
        print("order_request[0])


        # Remaining reorder requests for all BMart stores
    
        total_price = 0
        for reorder in reorder_list:
            # getting the count of each product id
            product_count = "SELECT amount_requested FROM order_request WHERE request_id = %s"
            params1 = (reorder,)
            cursor.execute(product_count, params1)
            num_requested = cursor.fetchone()
            num_requested = num_requested[0]
            product_price = "SELECT sell_price FROM price JOIN order_group ON price.product_id = order_group.product_id"
            product_price += " WHERE request_id = %s"
            params3 = (reorder,)
            cursor.execute(product_price, params3)
            product_price = cursor.fetchone()
            product_price = product_price[0]
            total_price = total_price + (product_price * num_requested)
            # for item in shipment_items:
            #     # use specific column names when selecting, * is baddddd 
            #     get_product = "SELECT * FROM price WHERE product_id = %s"
            #     params = (item,)
            #     cursor.execute(get_product, params)
            #     get_vendor = cursor.fetchone()
          

            # probably going to lose point because this is bad for longevity, use names instead 
            # stores unit price of vendor for each product_id
            

            # total_price = get_vendor + total_price
            


    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            cnx.rollback()
            print(err)
    else:
        cnx.close()

vendor_shipment(94, '2022-12-18', [483, 943, 31323], '30 mint oreos; 45 double stuff oreos; 90 regular oreos')

def stockInventory(store,shipment,shipment_items):
    try:
        cnx = mysql.connector.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            cnx.rollback()
            print(err)
    else:
        cnx.close()


def OnlineOrder(store,customer,order_items):
    try:
        cnx = mysql.connector.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')
        cursor = cnx.cursor(buffered=True)
        for item in order_items:
            online_order = "SELECT * FROM inventory_space WHERE product_id = %s"
            cursor.execute(online_order, (item,))
            product = cursor.fetchone()


    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            cnx.rollback()
            print(err)
    else:
        cnx.close()


reorder(1)
