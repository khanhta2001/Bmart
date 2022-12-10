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
        store_name = cursor.fetchone()
        if store_name is None:
            print("Store does not exist")
            return
        store_inventory = "SELECT * FROM inventory_space WHERE store_id = %s"
        cursor.execute(store_inventory, (store,))
        store_items = cursor.fetchone()
        item_price = "SELECT * FROM price WHERE product_id = %s"
        # This currently orders the same item over and over again
        # should probably add loop to add several items
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
                # Add a check to see if the request id is equivalent to the request we are working
                orders_rem = "SELECT store_id FROM order_request WHERE store_id = %s AND order_status = 0"
                params5 = (store,)
                cursor.execute(orders_rem, params5)
                store_order_request = cursor.fetchall()
                total_amount = 0
                if len(store_order_request) == 0:
                    if total_amount + current_stock < max_stock:
                        print("Reorder is needed")
                        reorder_amount = max_stock - current_stock - total_amount
                        print("Reorder amount is:", reorder_amount)
                        reorder_query = (
                            "INSERT INTO order_request (vendor_id, store_id, amount_requested, order_time, "
                            "total_cost, order_status,seen_or_not) VALUES (%s,%s, %s, %s, %s, %s, %s)")
                        params = (
                            vendor, store, reorder_amount, datetime.datetime.now(), product_price * reorder_amount, 0,
                            0)
                        cursor.execute(reorder_query, params)
                        last_row = cursor.lastrowid
                        order_group = ("INSERT INTO order_group (request_id, product_id) VALUES (%s, %s)")
                        param = (last_row, store_items[0])
                        cursor.execute(order_group, param)
                        cnx.commit()
                        return
                    else:
                        print('There is no need to reorder')
                        return
                else:
                    print("Order requests are already made")
                    return
            except mysql.connector.Error as err:
                cnx.rollback()
                print("Something went wrong: {}".format(err))
                return
    except mysql.connector.Error as err:
        cnx.rollback()
        print("Something went wrong: {}".format(err))
        cnx.close()
        return


def vendor_shipment(store, delivery_time, reorder_list, shipment_items):
    try:
        cnx = mysql.connector.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')
        cursor = cnx.cursor(buffered=True)
        # The shipments must be inserted into the database
        # Print a list of all the products in the shipment
        all_items = ''
        list_of_items = []
        for item in shipment_items:
            # add a name field to product table
            get_product = "SELECT product_name FROM product WHERE product_id = %s"
            params = (item,)
            cursor.execute(get_product, params)
            product_name = cursor.fetchone()
            if product_name is not None:
                all_items += product_name[0] + ' '
                list_of_items.append(product_name[0])
            else:
                print("Product {} does not exist".format(item))
        print(all_items)

        # Remaining reorder requests for this store particularly
        order_completed = {}
        for request_id in reorder_list:
            orders_rem = "SELECT order_request.request_id,order_request.amount_requested, order_group.product_id, " \
                         "order_request.vendor_id FROM " \
                         "order_request JOIN order_group ON order_request.request_id = order_group.request_id WHERE " \
                         "order_request.store_id = %s AND order_request.request_id = %s AND " \
                         "order_request.order_status = 0 "
            params5 = (store, request_id)
            cursor.execute(orders_rem, params5)
            order_request = cursor.fetchone()
            if order_request is not None:
                print("This order {} will be completed".format(order_request[0]))
                order_completed[order_request[0]] = order_request[3]
                update_order = "UPDATE order_request SET seen_or_not = 1 AND order_status = 1 WHERE request_id = %s"
                params = (order_request[0],)
                cursor.execute(update_order, params)
                cnx.commit()
            else:
                print("This order {} does not exist".format(request_id))

        # Remaining reorder requests for all BMart stores
        all_remaining_orders = "SELECT COUNT(request_id) FROM order_request WHERE order_status = 0"
        cursor.execute(all_remaining_orders)
        remaining_orders = cursor.fetchone()
        if remaining_orders[0] - len(order_completed) == 0:
            print("All orders are completed")
        else:
            print(remaining_orders[0] - len(order_completed), "orders are remaining")
        for request_id in order_completed:
            bruh = order_completed[request_id]

            shipment_request = "INSERT INTO shipment (expected_delivery_time, delivery_time,request_id, vendor_id) VALUES (%s, %s, %s, %s)"
            params = (delivery_time, 0, request_id, order_completed[request_id])
            cursor.execute(shipment_request, params)
            cnx.commit()
            last_row = cursor.lastrowid
            shipment_group = "INSERT INTO shipment_group (shipment_id, request_id) VALUES (%s, %s)"
            params = (last_row, request_id)
            cursor.execute(shipment_group, params)
            cnx.commit()
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


vendor_shipment(1, datetime.datetime.now(), [1,2,3], {1: 20, 2: 20, 3: 4})


def stockInventory(store, shipment, shipment_items):
    try:
        cnx = mysql.connector.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')
        cursor = cnx.cursor(buffered=True)
        # Details about the shipment that was just received, number of each product and product name that are supposed to be in shipment
        product_list = "SELECT product_id, name, amount_requested FROM product JOIN order_group ON order_group.product_id = product.product_id"
        product_list += "JOIN order_request ON order_group.request_id = order_request.product_id JOIN shipment_group on shipment_group.request_id = order_request.request_id"
        product_list += "WHERE shipment_id = %s"
        cursor.execute(product_list, (shipment,))
        for (name, amount_requested) in cursor:
            print({}, {}).format(amount_requested, name)

        # Details about the shipment that was just received, number of each and product names that were actually received
        unique_products = set[shipment_items]
        for product in unique_products:
            num_of_item = shipment_items.count(product)
            product_name = "SELECT name FROM product WHERE product_id = %s"
            cursor.execute(product_name, (product,))
            for name in cursor:
                print(num_of_item, "of", {}).format(name)

            # shipment_items will be a list of product ids

            # count the number of

        # A list of the differences between what the shipment was supposed to contain and what it actually contained





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


def OnlineOrder(store, customer, order_items):
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
