import datetime

import mysql.connector
from mysql.connector import errorcode

#bruh 
def reorder(store):
    """
    This function is used to reorder products for a store.  It will check the reorder point and reorder amount for each product
    :param store: the store id, an integer
    :return:
    """
    try:
        # connect with the database
        cnx = mysql.connector.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')
        cursor = cnx.cursor(buffered=True)
        query = "SELECT * FROM store WHERE store_id = %s"
        params = (store,)
        cursor.execute(query, params)
        store_name = cursor.fetchone()
        # check if the store exists
        if store_name is None:
            print("Store id {} does not exist".format(store))
            return
        # check inventory of the store
        store_inventory = "SELECT product_id, maximum_space, current_stock FROM inventory_space WHERE store_id = %s"
        cursor.execute(store_inventory, (store,))
        store_items = cursor.fetchall()
        reordered_items = {}
        vendor_reorder = {}
        reorder_price = {}
        reorder_request = False
        # check store items and reorder if needed
        for store_item in store_items:
            item_price = "SELECT vendor_id,sell_price FROM price WHERE product_id = %s"
            cursor.execute(item_price, (store_item[0],))
            price = cursor.fetchone()
            vendor = price[0]
            product_price = price[1]
            current_stock = store_item[2]
            max_stock = store_item[1]
            # check if the item needs to be reordered
            if current_stock == max_stock:
                print("There is no need to reorder")
            else:
                # Add a check to see if the request id is equivalent to the request we are working
                item_reorder = "SELECT request_id FROM order_group WHERE product_id = %s"
                cursor.execute(item_reorder, (store_item[0],))
                item_reorder = cursor.fetchall()
                total_amount = 0
                # check if the item has been ordered before
                if len(item_reorder) != 0:
                    for request_id in item_reorder:
                        orders_rem = "SELECT amount_requested FROM order_request WHERE store_id = %s AND request_id = %s AND order_status = 0"
                        params5 = (store, request_id[0])
                        cursor.execute(orders_rem, params5)
                        amount = cursor.fetchone()
                        # Get total amount of the item from orders
                        total_amount += amount[0]
                # check if the item needs to be reordered
                if total_amount + current_stock < max_stock:
                    reorder_request = True
                    reorder_amount = max_stock - current_stock - total_amount
                    reordered_items[store_item[0]] = reorder_amount
                    # insert into the database to keep track of the order
                    reorder_query = (
                        "INSERT INTO order_request (vendor_id, store_id, amount_requested, order_time, "
                        "total_cost, order_status,seen_or_not) VALUES (%s,%s, %s, %s, %s, %s, %s)")
                    params = (
                        vendor, store, reorder_amount, datetime.datetime.now(), product_price * reorder_amount, 0,
                        0)
                    cursor.execute(reorder_query, params)
                    # insert into the database for order_group to keep track of the order
                    last_row = cursor.lastrowid
                    order_group = ("INSERT INTO order_group (request_id, product_id) VALUES (%s, %s)")
                    param = (last_row, store_item[0])
                    cursor.execute(order_group, param)
                    cnx.commit()
                    # get total price so we can print it out to console
                    reorder_price[store_item[0]] = product_price * reorder_amount
                    # get all the vendors reorders
                    if vendor in vendor_reorder:
                        vendor_reorder[vendor] += 1
                    else:
                        vendor_reorder[vendor] = 1
                else:
                    print('There is no need to reorder')
        # print out the reorder if there is a need to reorder
        if reorder_request:
            print("The following items have been reordered:{}".format(reordered_items))
            print("The following vendors have reorder requests:{}".format(vendor_reorder))
            print("Total price of each reorder request:{}".format(reorder_price))
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        return
    else:
        cnx.rollback()
        cnx.close()
        return


def vendor_shipment(store, delivery_time, reorder_list, shipment_items):
    """
    This function is used to create a shipment for a vendor
    :param store: the store id, an integer
    :param delivery_time: the delivery time, using datetime type
    :param reorder_list: the reorder list containing all request_id, a list of integers
    :param shipment_items: the shipment items where it contains product id and its amount, a dictionary of integers
    :return:
    """

    try:
        cnx = mysql.connector.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')
        cursor = cnx.cursor(buffered=True)
        query = "SELECT * FROM store WHERE store_id = %s"
        params = (store,)
        cursor.execute(query, params)
        store_name = cursor.fetchone()
        # check if the store exists
        if store_name is None:
            print("Store id {} does not exist".format(store))
            return
        invalid_product = 0
        for item in shipment_items:
            # add a name field to product table
            get_product = "SELECT order_group.request_id, order_request.store_id FROM order_group JOIN order_request ON order_group.request_id = order_request.request_id WHERE order_group.product_id = %s AND order_request.store_id = %s AND order_request.order_status = 0"
            params = (item,store)
            cursor.execute(get_product, params)
            product_name = cursor.fetchone()
            # if the item is not in the order group table
            if product_name is None:
                print("Invalid shipment item {}!. This item is not needed for this order".format(item))
                invalid_product += 1
        # Remaining reorder requests for this store particularly
        order_completed = {}
        if invalid_product > 0:
            return
        # update the order request as seen by vendor and will be completed
        for request_id in reorder_list:
            check_shipment = "SELECT request_id, delivery_time FROM shipment WHERE request_id = %s"
            params = (request_id,)
            cursor.execute(check_shipment, params)
            shipment = cursor.fetchone()
            # check if the shipment has been made
            if shipment is not None:
                if shipment[1] == 0:
                    print("This shipment has already been made")
                    cnx.rollback()
                    cnx.close()
                    return
            orders_rem = "SELECT order_request.request_id,order_request.amount_requested, order_group.product_id, " \
                         "order_request.vendor_id FROM " \
                         "order_request JOIN order_group ON order_request.request_id = order_group.request_id WHERE " \
                         "order_request.store_id = %s AND order_request.request_id = %s AND " \
                         "order_request.order_status = 0 "
            params5 = (store, request_id)
            cursor.execute(orders_rem, params5)
            order_request = cursor.fetchone()
            if order_request is not None:
                order_completed[order_request[0]] = order_request[3]
                update_order = "UPDATE order_request SET seen_or_not = 1, order_status = 1 WHERE request_id = %s"
                params = (order_request[0],)
                cursor.execute(update_order, params)
                cnx.commit()
            else:
                print("There are no orders to be completed")
                cnx.rollback()
                cnx.close()
                return
        vendor_store = {}
        vendor_bmart = {}
        # get the vendor id and store id
        for request_id in order_completed:
            vendor_id = order_completed[request_id]
            # insert into shipment table and marked as shipped
            shipment_request = "INSERT INTO shipment (expected_delivery_time, delivery_time,request_id, vendor_id, store_id) VALUES (%s, %s, %s, %s, %s)"
            params = (delivery_time, 0, request_id, vendor_id, store)
            cursor.execute(shipment_request, params)
            cnx.commit()
            last_row = cursor.lastrowid

            # insert into shipment_group table to track the shipment
            shipment_group = "INSERT INTO shipment_group (shipment_id, request_id) VALUES (%s, %s)"
            params = (last_row, request_id)
            cursor.execute(shipment_group, params)
            cnx.commit()
            print("Shipment request from vendor_id {} has been sent to store_id {}".format(vendor_id, store))
            # Remaining reorder requests for specific store from that specific vendor
            vendor_remaining_orders = "SELECT COUNT(request_id) FROM order_request WHERE order_status = 0 AND vendor_id = %s AND store_id = %s AND request_id != %s"
            cursor.execute(vendor_remaining_orders, (vendor_id, store, request_id))
            vendor_store_remaining_orders = cursor.fetchone()

            # Remaining reorder requests for all BMart stores from that specific vendor
            vendor_remaining_orders = "SELECT COUNT(request_id) FROM order_request WHERE order_status = 0 AND vendor_id = %s AND request_id != %s"
            cursor.execute(vendor_remaining_orders, (vendor_id, request_id))
            vendor_bmart_remaining_orders = cursor.fetchone()

            # if the vendor has no more orders for that store
            if vendor_id not in vendor_store or vendor_store_remaining_orders[0] != 0:
                vendor_store[vendor_id] = vendor_store_remaining_orders[0]
            if vendor_id not in vendor_bmart or vendor_bmart_remaining_orders[0] != 0:
                vendor_bmart[vendor_id] = vendor_bmart_remaining_orders[0]

        # print out the remaining orders for the vendor and that specific store
        if len(vendor_store) > 0:
            print("Remaining reorder requests for this store: {}".format(vendor_store))
        else:
            print("There are no remaining reorder requests for this store")

        # print out the remaining orders for the vendor and all BMart stores
        if len(vendor_bmart) > 0:
            print("Remaining reorder requests for all BMart stores: {}".format(vendor_bmart))
        else:
            print("There are no remaining reorder requests for all BMart stores")

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        cnx.close()


def stockInventory(store, shipment, shipment_items):
    """
    This function is used to update the stock inventory when a shipment has arrived
    :param store: store_id, an integer
    :param shipment: shipment_id, an integer
    :param shipment_items: shipment_items, a dictionary of integers
    :return:
    """
    try:
        cnx = mysql.connector.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')
        cursor = cnx.cursor(buffered=True)
        query = "SELECT * FROM store WHERE store_id = %s"
        params = (store,)
        cursor.execute(query, params)
        store_name = cursor.fetchone()
        # check if the store exists
        if store_name is None:
            print("Store id {} does not exist".format(store))
            return
        # check if the shipment exists
        shipment_info = "SELECT shipment.shipment_id, shipment.vendor_id, shipment.store_id, order_group.product_id FROM shipment JOIN " \
                         "order_request ON shipment.request_id = order_request.request_id JOIN order_group ON " \
                         "order_request.request_id = order_group.request_id WHERE shipment.shipment_id = %s "
        params = (shipment,)
        cursor.execute(shipment_info, params)
        shipment_info = cursor.fetchone()
        if shipment_info is None:
            print("Invalid shipment! Shipment id {} does not exist".format(shipment))
            return
        difference_amount = {}
        shipment_success = False
        invalid_product = 0
        for item in shipment_items:
            # Check if the shipment item is in the shipment
            get_product = "SELECT order_group.product_id, order_request.amount_requested  FROM shipment JOIN order_group ON shipment.request_id = order_group.request_id JOIN order_request ON shipment.request_id = order_request.request_id WHERE order_group.product_id = %s AND shipment.shipment_id = %s"
            params = (item, shipment)
            cursor.execute(get_product, params)
            product_info = cursor.fetchone()
            if product_info is None:
                print("Invalid shipment item {}!. This item is not in the shipment".format(item))
                invalid_product += 1

        if invalid_product != 0:
            return
        for item in shipment_items:
            # Check if the shipment item is in the shipment
            get_product = "SELECT order_group.product_id, order_request.amount_requested  FROM shipment JOIN order_group ON shipment.request_id = order_group.request_id JOIN order_request ON shipment.request_id = order_request.request_id WHERE order_group.product_id = %s AND shipment.shipment_id = %s"
            params = (item, shipment)
            cursor.execute(get_product, params)
            product_info = cursor.fetchone()
            # check the difference between the shipment item and the amount requested
            if product_info[1] < shipment_items[item]:
                print("The amount requested for product id {} is less than the amount received".format(item))
                difference_amount[item] = shipment_items[item] - product_info[1]
            elif product_info[1] > shipment_items[item]:
                print("The amount requested for product id {} is more than the amount received".format(item))
                difference_amount[item] = shipment_items[item] - product_info[1]
            # Check the stock inventory for the product
            current_stock = "SELECT current_stock, maximum_space FROM inventory_space WHERE store_id = %s AND product_id = %s"
            params = (store, item)
            cursor.execute(current_stock, params)
            current_stock = cursor.fetchone()
            # check the total amount of stock inventory for the product
            if current_stock[0] + shipment_items[item] > current_stock[1]:
                print("The amount of product id {} in the inventory space is more than maximum space".format(item))
                print("This shipment will be rejected")
                return

            # update the stock inventory for the product if the total amount is less than the maximum space
            stock = "UPDATE inventory_space SET current_stock = %s WHERE product_id = %s and store_id = %s"
            params = (current_stock[0] + shipment_items[item], item, store)
            cursor.execute(stock, params)
            cnx.commit()

            # update the shipment status to received at the time of the shipment
            update_shipment_info = "UPDATE shipment SET delivery_time = %s WHERE shipment_id = %s"
            shipped_time = datetime.datetime.now() + datetime.timedelta(days=2)
            params = (shipped_time, shipment)
            cursor.execute(update_shipment_info, params)
            cnx.commit()
            shipment_success = True

        # if the shipment is successful
        if shipment_success:
            print("Shipment {} has been received".format(shipment))
            print("Shipment information is as follows: shipment id: {}, vendor id: {}, arrived time: {}, product id: {}, amount requested: {}".format(shipment_info[0], shipment_info[1], shipped_time, shipment_info[3], shipment_items[shipment_info[3]]))

        # If there is a difference between the amount requested and the amount sent by vendor, print it to console
        if len(difference_amount) > 0:
            print("The following items have a difference amount: {}".format(difference_amount))

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


# order_items is a dictionary where key is product and value is amount ordered
def OnlineOrder(store, customer, order_items):
    """
    This function is used to place an online order by a customer
    :param store: store_id, an integer
    :param customer: customer_id, an integer
    :param order_items: order_items, a dictionary of integers where key is product_id and value is quantity
    :return:
    """
    try:
        cnx = mysql.connector.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')
        cursor = cnx.cursor(buffered=True)

        in_stock = 0
        # check if each of the product in the order are in stock in the current store
        for item in order_items:
            inventory = "SELECT current_stock FROM inventory_space AS i WHERE i.product_id = %s AND i.store_id = %s"
            cursor.execute(inventory, (item, store))
            product_inventory = cursor.fetchone()
            # if an invalid product is entered, give the customer a warning message
            if product_inventory == None:
                print('Invalid product! Product id {} does not exist in the store'.format(item))
            else:    
                # get the name of the product from product table so if it's out of stock we can tell the customer
                name = "SELECT product_name FROM product WHERE product_id = %s"
                cursor.execute(name, [item])
                product_name = cursor.fetchone()

                # if current stock of a product is less than the amount the customer entered
                if product_inventory[0] < order_items[item]:
                    # give error message
                    print('Purchase failed because ' + product_name + ' is out of stock at this store')
                    # and see if any other store in the same state has the product
                    address = "SELECT state FROM store where store_id = %s"
                    cursor.execute(address, (store))
                    current_state = cursor.fetchone()[0]
                    stock = "SELECT store_id FROM store WHERE state = %s"
                    cursor.execute(stock, [current_state])
                    available_store = cursor.fetchone()[0]
                    print("This product is in stock in store " + available_store)
                    break

                in_stock += 1
 
        # if all the products are in stock, continue with the transaction
        if in_stock == len(order_items):
            for item in order_items:
                # decrease current stock of the product
                inventory = "SELECT current_stock FROM inventory_space AS i WHERE i.product_id = %s AND i.store_id = %s"
                cursor.execute(inventory, (item, store))
                product_inventory = cursor.fetchone()
                new_stock = product_inventory[0] - order_items[item]
                change = "UPDATE inventory_space SET current_stock = %s WHERE product_id = %s and store_id = %s"
                cursor.execute(change, [new_stock, item, store])

            # record the order in the database
            record = "INSERT INTO customer_order (order_type, customer_id, store_id) VALUES (%s, %s, %s)"
            cursor.execute(record, ('online', customer, store))
            # give the customer information on the order they just made

            print('Order successfully placed!')

            name = "SELECT customer_name FROM customers WHERE customer_id = %s"
            cursor.execute(name, [customer])
            customer_name = cursor.fetchone()[0]
            print('Customer name: ' + customer_name)

            phone = "SELECT phone_number FROM customers WHERE customer_id = %s"
            cursor.execute(phone, [customer])
            customer_phone = cursor.fetchone()[0]
            print('Customer contact: ' + str(customer_phone))

            address = "SELECT address FROM customers WHERE customer_id = %s"
            cursor.execute(address, [customer])
            customer_address = cursor.fetchone()[0]
            print('Customer Address: ' + customer_address)

            total_price = 0
            # A list of the ordered items and their quantities
            print('Ordered items: ') 
            for item in order_items:
                # get the name of the product from product table 
                name = "SELECT product_name FROM product WHERE product_id = %s"
                cursor.execute(name, [item])
                product_name = cursor.fetchone()[0]
                print(product_name + ', quantity: ' + str(order_items[item]))

                price = "SELECT override_price FROM store_price WHERE store_id = %s AND product_id = %s"
                cursor.execute(price, [store, item])
                item_price = cursor.fetchone()[0]
                total_price += item_price
            
            # The total price for that order, based on the current store price for each of those items.
            print('Total price: ' + str(total_price))

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        cnx.close()

#OnlineOrder(1, 1, {1: 1})
# reorder(1)
# reorder(2)
vendor_shipment(1, datetime.datetime.now() + datetime.timedelta(days=2), [1, 2, 3], {1: 20})
# stockInventory(1,1, {1: 20, 2: 20, 3: 4})
