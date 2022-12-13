import datetime

import mysql.connector
from mysql.connector import errorcode


def reorder(store):
    """
    This function is used to reorder products for a store. It will check if new reorder requests are needed and if so send the requests.
    :param store: the store id, an integer
    :return:
    """
    try:
        # connect with the database
        cnx = mysql.connector.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')
        cursor = cnx.cursor(buffered=True)
        query = "SELECT * FROM store WHERE store_id = %s"
        cursor.execute(query, [store])
        store_info = cursor.fetchone()
        # check if the store exists, if not whole order is rolled back
        if store_info is None:
            print("Store id {} does not exist".format(store))
            return

        # if store exists, check inventory of the store to see if more orders need to be made
        store_inventory = "SELECT product_id, maximum_space, current_stock FROM inventory_space WHERE store_id = %s"
        cursor.execute(store_inventory, [store])
        store_items = cursor.fetchall()

        reordered_items = {}
        vendor_reorder = {}
        reorder_request = False

        # check if reorder is needed for each store item
        full_stock_items = []
        need_reorder_items = []
        total_price = 0
        for store_item in store_items:
            item_price = "SELECT vendor_id, sell_price FROM price WHERE product_id = %s"
            cursor.execute(item_price, [store_item[0]])
            vendor_price = cursor.fetchone()
            # check if the item is invalid, if not the whole reorder should be rolled back
            if vendor_price == None:
                print("Product id {} is invalid!".format(store_item[0]))
                return
            # if the item is valid, continue with reorder
            vendor_id = vendor_price[0]
            product_price = vendor_price[1]
            max_stock = store_item[1]
            current_stock = store_item[2]

            # if current stock for an item is less than maximum space, then continue with reorder
            if current_stock < max_stock:
                # get all existing request amounts by the store for the product
                amount_requested = "SELECT order_group.amount_requested FROM order_group JOIN order_request ON order_group.request_id = order_request.request_id WHERE order_request.store_id = %s AND order_group.product_id = %s AND order_request.order_status = 0"
                cursor.execute(amount_requested, [store, store_item[0]])
                amount_requested = cursor.fetchall()

                total_requested = 0
                if amount_requested != None:
                    for amount in amount_requested:
                        total_requested += amount[0]

                # if existing requests are not enough to fill the stock, we need to make new requests
                if total_requested + current_stock < max_stock:
                    reorder_request = True
                    need_reorder_items.append(store_item[0])
                    new_reorder_amount = max_stock - current_stock - total_requested
                    reordered_items[store_item[0]] = new_reorder_amount  # amount for the new request

                    '''
                    get_row = "SELECT request_id FROM order_request"
                    cursor.execute(get_row)
                    request_id = cursor.rowcount + 1
                    '''

                    # insert into order_request table
                    reorder_query = (
                        "INSERT INTO order_request (vendor_id, store_id, total_cost, order_status, seen_or_not) "
                        " VALUES (%s, %s, %s, %s, %s)")
                    params = (vendor_id, store, product_price * new_reorder_amount, 0, 0)
                    cursor.execute(reorder_query, params)

                    # get the request_id of the request we just inserted
                    request_id = "SELECT request_id FROM order_request ORDER BY request_id DESC LIMIT 1"
                    cursor.execute(request_id)
                    request_id = cursor.fetchone()[0]

                    # insert into order_group table
                    order_group = (
                        "INSERT INTO order_group (request_id, product_id, amount_requested) VALUES (%s, %s, %s)")
                    param = (request_id, store_item[0], new_reorder_amount)
                    cursor.execute(order_group, param)
                    cnx.commit()

                    # get total price of this reorder
                    total_price += product_price * new_reorder_amount

                    # increment orders with each of the vendors
                    if vendor_id in vendor_reorder:
                        vendor_reorder[vendor_id] += 1
                    else:
                        vendor_reorder[vendor_id] = 1

                # if existing reorder requests are enough to fill the stock for an item
                else:
                    full_stock_items.append(store_item[0])

            # if stock is already full for an item
            elif current_stock == max_stock:
                full_stock_items.append(store_item[0])

        if len(full_stock_items) == len(store_items):
            print('No need to reorder, all items are full or have enough existing orders')
        else:
            for item in full_stock_items:
                print('Reorder request is not needed for the item {}'.format(item))

        # print out the reorder if there is a need to reorder
        if reorder_request:
            print("The following items have been reordered: {}".format(reordered_items))
            print("The following vendors have reorder requests: {}".format(vendor_reorder))
            print("Total price of the reorder requests: {}".format(total_price))

    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        return
    else:
        cursor.close()
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

        # check if the store exists
        query = "SELECT * FROM store WHERE store_id = %s"
        params = (store,)
        cursor.execute(query, params)
        store_name = cursor.fetchone()
        if store_name is None:
            print("Store id {} does not exist".format(store))
            return

        vendor_store = {}
        vendor_bmart = {}
        invalid_product = 0
        vendors = {}
        for item in shipment_items:
            # add a name field to product table
            get_product = "SELECT order_request.store_id, order_request.vendor_id FROM order_group JOIN " \
                          "order_request ON order_group.request_id = order_request.request_id WHERE " \
                          "order_group.product_id = %s AND order_request.store_id = %s" \
                          " AND order_request.order_status = 0 "
            params = (item, store)
            cursor.execute(get_product, params)
            product_name = cursor.fetchone()
            # if the item is not in the order group table
            if product_name is None:
                print("Invalid shipment item {}!. This item is not needed for this order".format(item))
                invalid_product += 1
            else:
                if product_name[1] in vendors:
                    vendors[product_name[1]].append(item)
                else:
                    vendors[product_name[1]] = [item]

        # if there is invalid product, stop the function
        if invalid_product > 0:
            return
        for request_id in reorder_list:
            # check if the items are all valid
            request_order = "SELECT request_id FROM order_request WHERE request_id = %s"
            cursor.execute(request_order, [request_id])
            request_order = cursor.fetchone()
            if request_order is None:
                print("Request id {} does not exist".format(request_id))
                return
            # update the order request as seen by vendor and will be completed
            for vendor_id in vendors:
                # check if the shipment has been made by the same vendor for the same store
                check_shipment = "SELECT request_id FROM shipment WHERE request_id = %s AND vendor_id = %s AND store_id = %s"
                params = (request_id, vendor_id, store)
                cursor.execute(check_shipment, params)
                shipment = cursor.fetchone()
                # check if the shipment has been made
                if shipment is not None:
                    print("This shipment has already been made")
                    cnx.rollback()
                    cnx.close()
                    return
                # insert into shipment_group table to track the shipment
                for item in vendors[vendor_id]:
                    # check if the item in request id matches with vendor items
                    match_product_request = "SELECT product_id FROM order_group WHERE product_id = %s AND request_id = %s"
                    params = (item, request_id)
                    cursor.execute(match_product_request, params)
                    match_product_request = cursor.fetchone()
                    # if matches then go ahead and insert into shipment_group table
                    if match_product_request is not None:
                        get_row = "SELECT shipment_id FROM shipment JOIN order_group ON order_group.request_id = " \
                                  "shipment.request_id WHERE shipment.store_id = %s AND shipment.expected_delivery_time = " \
                                  "%s"
                        cursor.execute(get_row, [store, delivery_time])
                        shipment_store = cursor.fetchone()
                        if shipment_store is None:
                            get_row = "SELECT shipment_id FROM shipment"
                            cursor.execute(get_row)
                            shipment_id = cursor.fetchall()
                            shipment_store = [len(shipment_id) + 1]
                        # insert into shipment table and marked as shipped
                        shipment_request = "INSERT INTO shipment (shipment_id, expected_delivery_time, delivery_time,request_id, " \
                                           "vendor_id, store_id) VALUES (%s, %s, %s, %s, %s, %s) "
                        params = (shipment_store[0], delivery_time, 0, request_id, vendor_id, store)
                        cursor.execute(shipment_request, params)

                        shipment_group = "INSERT INTO shipment_group (shipment_id, request_id, product_id) VALUES (%s, %s, %s)"
                        params = (shipment_store[0], request_id, item)
                        cursor.execute(shipment_group, params)

                        # update the order request as seen by vendor and will be completed
                        update_order = "UPDATE order_request SET seen_or_not = 1 WHERE request_id = %s"
                        params = (request_id,)
                        cursor.execute(update_order, params)

                        print("Shipment request from vendor_id {} has been sent to store_id {}".format(vendor_id, store))
                        cnx.commit()

                # Remaining reorder requests for specific store from that specific vendor
                vendor_remaining_orders = "SELECT COUNT(request_id) FROM order_request WHERE order_status = 0 AND " \
                                          "vendor_id = %s AND store_id = %s AND request_id != %s "
                cursor.execute(vendor_remaining_orders, (vendor_id, store, request_id))
                vendor_store_remaining_orders = cursor.fetchone()

                # Remaining reorder requests for all BMart stores from that specific vendor
                vendor_remaining_orders = "SELECT COUNT(request_id) FROM order_request WHERE order_status = 0 AND " \
                                          "vendor_id = %s AND request_id != %s "
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
            cnx.rollback()
    else:
        cnx.close()


def stock_inventory(store, shipment, shipment_items):
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

        # check if the store exists
        query = "SELECT * FROM store WHERE store_id = %s"
        params = (store,)
        cursor.execute(query, params)
        store_name = cursor.fetchone()
        if store_name is None:
            print("Store id {} does not exist".format(store))
            return

        # check if the shipment exists
        shipment_info = "SELECT shipment.shipment_id, shipment.vendor_id, shipment.store_id, order_group.product_id FROM shipment JOIN " \
                        "order_request ON shipment.request_id = order_request.request_id JOIN order_group ON " \
                        "order_request.request_id = order_group.request_id WHERE shipment.shipment_id = %s and order_request.order_status = 0"
        params = (shipment,)
        cursor.execute(shipment_info, params)
        shipment_info = cursor.fetchone()
        if shipment_info is None:
            print("Invalid shipment! Shipment id {} does not exist".format(shipment))
            return

        difference_amount = {}
        shipment_success = False
        invalid_product = 0
        shipped_time = 0
        products = []

        # check each item in shipment items is a valid item in the shipment
        for item in shipment_items:
            # Check if the shipment item is in the shipment
            get_product = "SELECT order_group.product_id, order_group.amount_requested, " \
                          "shipment.expected_delivery_time, order_request.request_id  FROM shipment JOIN order_group " \
                          "ON shipment.request_id = order_group.request_id JOIN order_request ON shipment.request_id " \
                          "= order_request.request_id WHERE order_group.product_id = %s AND shipment.shipment_id = %s "
            params = (item, shipment)
            cursor.execute(get_product, params)
            product_info = cursor.fetchone()
            products.append(product_info)
            if product_info is None:
                print("Invalid shipment item {}!. This item is not in the shipment".format(item))
                invalid_product += 1
            check_item = "SELECT product_id FROM inventory_space WHERE store_id = %s AND product_id = %s"
            params = (store, item)
            cursor.execute(check_item, params)
            item_info = cursor.fetchone()
            if item_info is None:
                print("Invalid shipment item {}!. This item does not belong to the store".format(item))
                invalid_product += 1

        # if there is invalid product, return
        if invalid_product != 0:
            return

        # if all the products are valid, update the stock inventory
        for product_info in products:
            # check the difference between the shipment item and the amount requested
            item_amount = shipment_items[product_info[0]]
            if product_info[1] < item_amount:
                print("The amount requested for product id {} is less than the amount received".format(product_info[0]))
                difference_amount[product_info[0]] = item_amount - product_info[1]
            elif product_info[1] > item_amount:
                print("The amount requested for product id {} is more than the amount received".format(product_info[0]))
                difference_amount[product_info[0]] = product_info[1] - item_amount

            # Check the stock inventory for the product
            current_stock = "SELECT current_stock, maximum_space FROM inventory_space WHERE store_id = %s AND " \
                            "product_id = %s "
            params = (store, product_info[0])
            cursor.execute(current_stock, params)
            current_stock = cursor.fetchone()
            # check the total amount of stock inventory for the product
            if current_stock[0] + item_amount > current_stock[1]:
                print("The amount of product id {} in the inventory space is more than maximum space".format(
                    product_info[0]))
                print("This shipment will be rejected")
                return
            # update the stock inventory for the product if the total amount is less than the maximum space
            stock = "UPDATE inventory_space SET current_stock = %s WHERE product_id = %s and store_id = %s"
            params = (current_stock[0] + item_amount, product_info[0], store)
            cursor.execute(stock, params)

            # update the shipment status to received at the time of the shipment
            update_shipment_info = "UPDATE shipment SET delivery_time = %s WHERE shipment_id = %s"
            shipped_time = product_info[2] + datetime.timedelta(days=2)
            params = (shipped_time, shipment)
            cursor.execute(update_shipment_info, params)

            # update the order request status to received
            update_order_request = "UPDATE order_request SET order_status = 1 WHERE request_id = %s"
            params = (product_info[3],)
            cursor.execute(update_order_request, params)
            shipment_success = True
        # if the shipment is successful
        if shipment_success:
            print("Shipment {} has been received".format(shipment))
            print("Shipment information is as follows: shipment id: {}, vendor id: {}, arrived time: {}, product id: "
                  "{}, amount requested: {}".format(shipment_info[0], shipment_info[1], shipped_time, shipment_info[3],
                                                    shipment_items[shipment_info[3]]))
            cnx.commit()

            # If there is a difference between the amount requested and the amount sent by vendor, print it to console
            if len(difference_amount) > 0:
                print("The following items have a difference amount: {}".format(difference_amount))
        else:
            print("Shipment {} has not been received".format(shipment))
            cnx.rollback()
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        cnx.close()


# order_items is a dictionary where key is product and value is amount ordered
def online_order(store, customer, order_items):
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
        query = "SELECT * FROM store WHERE store_id = %s"
        params = (store,)
        cursor.execute(query, params)
        store_name = cursor.fetchone()
        # check if the store exists
        if store_name is None:
            print("Store id {} does not exist".format(store))
            return
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
                    print('Purchase failed because ' + product_name[0] + ' is out of stock at this store')
                    # and see if any other store in the same state has the product
                    address = "SELECT state FROM store where store_id = %s"
                    params = (store,)
                    cursor.execute(address, params)
                    current_state = cursor.fetchone()[0]
                    stock = "SELECT store_id FROM store WHERE state = %s"
                    cursor.execute(stock, [current_state])
                    available_store = cursor.fetchone()
                    if available_store == None:
                        print('Unfortunately it is out of stock in all our stores in this state!')
                    else:
                        print("This product is in stock in store " + str(available_store[0]))
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
                item_price = cursor.fetchone()[0] * order_items[item]
                total_price += item_price

            # The total price for that order, based on the current store price for each of those items.
            print('Total price: ' + str(total_price))
            cnx.commit()
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        cnx.close()


# for i in range(5000):
#     online_order(1, 1, {1: 5})
# reorder(1)
# reorder(2)
# reorder(3)
# reorder(4)
# reorder(5)
# reorder(6)
vendor_shipment(1, datetime.datetime.now() + datetime.timedelta(days=2), [1, 2], {1: 20, 2: 20})
vendor_shipment(2, datetime.datetime.now() + datetime.timedelta(days=2), [3], {3: 20})
stock_inventory(1, 1, {1: 20, 2:20})


# Bonus functions

# What are the top-selling product at a store?
# takes in a store id as an int
# prints a message with a product id as an int
def top_selling_store (store):
    try:
        cnx = mysql.connector.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')
        cursor = cnx.cursor(buffered=True)
        top = "SELECT product_id FROM items AS i"
        "JOIN customer_order AS co ON i.order_id = co.order_id "
        "JOIN store AS s ON s.store_id = co.store_id"
        "WHERE store_id = %s"
        "GROUP BY product_id"
        "ORDER BY COUNT(item_id) LIMIT 1"
        cursor.execute(top, [store])
        top_selling = cursor.fetchone()[0]
        print('The top selling product in store ' + store + ' is ' + top_selling)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        cnx.close()


# What are the top-selling product in a state?
# takes in a two letted state as a string
# prints a message with a product id as an int
def top_selling_state(state):
    try:
        cnx = mysql.connector.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')
        cursor = cnx.cursor(buffered=True)
        top = "SELECT product_id FROM items AS i JOIN customer_order AS co ON i.order_id = co.order_id JOIN store AS s ON s.store_id = co.store_id WHERE state = %s GROUP BY product_id ORDER BY COUNT(item_id) LIMIT 1"
        cursor.execute(top, [state])
        top_selling = cursor.fetchone()[0]
        print('The top selling product in state ' + state + ' is ' + top_selling)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        cnx.close()

# Which store has generated the most revenue in a state?
# takes in a two letted state as a string
# prints a message with a store id as an int
def most_revenue(state):
    try:
        cnx = mysql.connector.connect(user='JSKK', password='cs314', host='cs314.iwu.edu', database='jskk')
        cursor = cnx.cursor(buffered=True)
        top = "SELECT store_id FROM store AS s"
        "JOIN customer_order AS co ON s.store_id = co.store_id"
        "JOIN items AS i ON i.order_id = co.order_id"
        "WHERE state = %s"
        "GROUP BY s.store_id"
        "ORDER BY SUM(cost) DESC LIMIT 1"
        cursor.execute(top, [state])
        most_revenue = cursor.fetchone()[0]
        print('The store that has made the most revenue in ' + state + ' is ' + most_revenue)
    except:
        print("Database does not exist")
    else:
        cnx.close()

#top_selling_state('IL')

