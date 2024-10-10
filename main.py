import pandas as pd
import os
import streamlit as st


class ExchangeApplication:
    def __init__(self):
        # execution report is a list of dictionaries with the following keys:
        # orderId,Cl. Ord. ID, Instrument, Side, ExecutionStatus(New, Filled, PartiallyFilled, Rejected), Quantity, Price, Reason
        self.execution_report =[]
        self.remaining_sell_orders = []
        self.remaining_buy_orders = []
    
    # let's create a function to write on execution report
    # all arguments are optional except order
    def write_on_execution_report(self, order, reason=None, quantity_filled=None, price=None, execution_status=None):
        dict_to_append = {
            'orderId': order['orderId'],
            'Cl. Ord. ID': order['Cl. Ord. ID'],
            'Instrument': order['Instrument'],
            'Side': order['Side'],
            'ExecutionStatus': execution_status if execution_status else 'New',
            'Quantity': quantity_filled if quantity_filled else order['Quantity'],
            'Price': price if price else order['Price'],
            'Reason for Rejection': reason if reason else ''
        }
        self.execution_report.append(dict_to_append)

    def submit_orders(self, orders):
        # let's give a orderId to each order
        orders['orderId'] = range(1, len(orders) + 1)
        
        for index, row in orders.iterrows():
            # check for validations
            if row['Cl. Ord. ID'] is None or row['Cl. Ord. ID'] == '' or len(row['Cl. Ord. ID']) >= 7:
                self.write_on_execution_report(row, reason='Invalid Cl. Ord. ID', execution_status='Rejected')
                continue
            if row['Instrument'] not in ['Rose', 'Lavender', 'Lotus', 'Tulip', 'Orchid']:
                self.write_on_execution_report(row, reason='Invalid Instrument', execution_status='Rejected')
                continue
            if row['Side'] not in [1, 2]:
                self.write_on_execution_report(row, reason='Invalid Side', execution_status='Rejected')
                continue
            # check for quantity min 10 and max 1000 and multiple of 10
            if row['Quantity'] < 10 or row['Quantity'] > 1000 or row['Quantity'] % 10 != 0:
                self.write_on_execution_report(row, reason='Invalid Quantity', execution_status='Rejected')
                continue
            if row['Price'] < 0:
                self.write_on_execution_report(row, reason='Invalid Price', execution_status='Rejected')
                continue
            
            if row['Side'] == 1:
                if len(self.remaining_sell_orders) > 0:
                    self.remaining_sell_orders.sort(key=lambda x: x['Price'])
                    for sell_order in self.remaining_sell_orders:
                        if row['Price'] >= sell_order['Price']:
                            if row['Quantity'] == sell_order['Quantity']:
                                self.write_on_execution_report(row, quantity_filled=row['Quantity'], price=sell_order['Price'], execution_status='Filled')
                                self.write_on_execution_report(sell_order, quantity_filled=sell_order['Quantity'], price=sell_order['Price'], execution_status='Filled')
                                self.remaining_sell_orders.remove(sell_order)
                                break
                            elif row['Quantity'] < sell_order['Quantity']:
                                self.write_on_execution_report(row, quantity_filled=row['Quantity'], price=sell_order['Price'], execution_status='PartiallyFilled')
                                self.write_on_execution_report(sell_order, quantity_filled=row['Quantity'], price=sell_order['Price'], execution_status='PartiallyFilled')
                                sell_order['Quantity'] -= row['Quantity']
                                break
                            elif row['Quantity'] > sell_order['Quantity']:
                                self.write_on_execution_report(row, quantity_filled=sell_order['Quantity'], price=sell_order['Price'], execution_status='PartiallyFilled')
                                self.write_on_execution_report(sell_order, quantity_filled=sell_order['Quantity'], price=sell_order['Price'], execution_status='Filled')
                                row['Quantity'] -= sell_order['Quantity']
                                self.remaining_sell_orders.remove(sell_order)
                                self.remaining_buy_orders.append(row.to_dict())
                                continue
                else:
                    self.write_on_execution_report(row, execution_status='New')
                    self.remaining_buy_orders.append(row.to_dict())
            else:
                if len(self.remaining_buy_orders) > 0:
                    # we have to sort the remaining buy orders in descending order
                    self.remaining_buy_orders = sorted(self.remaining_buy_orders, key=lambda x: x['Price'], reverse=True)
                    for buy_order in self.remaining_buy_orders:
                        if row['Price'] <= buy_order['Price']:
                            if row['Quantity'] == buy_order['Quantity']:
                                self.write_on_execution_report(row, quantity_filled=row['Quantity'], price=buy_order['Price'], execution_status='Filled')
                                self.write_on_execution_report(buy_order, quantity_filled=buy_order['Quantity'], price=buy_order['Price'], execution_status='Filled')
                                self.remaining_buy_orders.remove(buy_order)
                                break
                            elif row['Quantity'] < buy_order['Quantity']:
                                self.write_on_execution_report(row, quantity_filled=row['Quantity'], price=buy_order['Price'], execution_status='Filled')
                                self.write_on_execution_report(buy_order, quantity_filled=row['Quantity'], price=buy_order['Price'], execution_status='PartiallyFilled')
                                buy_order['Quantity'] -= row['Quantity']
                                break
                            elif row['Quantity'] > buy_order['Quantity']:
                                self.write_on_execution_report(row, quantity_filled=buy_order['Quantity'], price=buy_order['Price'], execution_status='PartiallyFilled')
                                self.write_on_execution_report(buy_order, quantity_filled=buy_order['Quantity'], price=buy_order['Price'], execution_status='Filled')
                                row['Quantity'] -= buy_order['Quantity']
                                self.remaining_buy_orders.remove(buy_order)
                                self.remaining_sell_orders.append(row.to_dict())
                                continue
                else:
                    self.write_on_execution_report(row, execution_status='New')
                    self.remaining_sell_orders.append(row.to_dict())
    
    def get_execution_report(self):
        df = pd.DataFrame(self.execution_report)
        return df

# trader application tasks are getting the orders from the user and pass it Exchange Application and get the excution report from exchange application give it to the user
class TraderApplication:
    def __init__(self):
        self.exchange_app = ExchangeApplication()
        
    def get_orders(self, orders=None):
        if orders is None:
            # get the orders from the user
            file_name = input("Enter the file name:")
            # file_name = "Orders.csv"
            if not os.path.exists(file_name):
                print(f"File {file_name} does not exist")
                exit(1)
            orders = pd.read_csv(file_name)
        else:
            orders = pd.read_csv(orders)
        
        # let's check the header of the orders
        if not 'Cl. Ord. ID' in orders.columns:
            print("Cl. Ord. ID column not found")
            exit(1)
        if not 'Instrument' in orders.columns:
            print("Instrument column not found")
            exit(1)
        if not 'Side' in orders.columns:
            print("Side column not found")
            exit(1)
        if not 'Quantity' in orders.columns:
            print("Quantity column not found")
            exit(1)
        if not 'Price' in orders.columns:
            print("Price column not found")
            exit(1)
        #  check if the orders are valid
        if orders.empty:
            print("No orders found")
            exit(1)
            
        self.orders = orders
        return orders
    
    def submit_orders(self):
        # submit the orders to the exchange application
        self.exchange_app.submit_orders(self.orders)

    def get_execution_report(self):
        # get the execution report from the exchange application
        self.execution_report = self.exchange_app.get_execution_report()
        return self.execution_report
    
    def write_on_csv(self):
        # write the execution report on csv file
        self.get_execution_report()
        self.execution_report.to_csv("ExecutionReport.csv", index=False)
        
trader_app = TraderApplication()
st.title("Trader Application")
file = st.file_uploader("Choose a file")
if file is not None:
    trader_app.get_orders(file)
    trader_app.submit_orders()
    trader_app.write_on_csv()
    st.success("Orders submitted successfully!. Execution report written on csv file")
    st.write("Execution report:")
    # we have to increase the width of the dataframe
    st.dataframe(trader_app.get_execution_report(), width=1000)
# trader_app.getOrders()
# trader_app.submit_orders()
# trader_app.write_on_csv()
# print("Execution report written on csv file")
# print(trader_app.get_execution_report())
