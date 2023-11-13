import requests
import json
import os
import openpyxl
from dotenv import load_dotenv

load_dotenv()

class Oanda:

    def __init__(self,access_token):
        self.access_token = access_token

        self.default_headers = {'Content-Type': 'application/json',
           'Authorization': f'Bearer {self.access_token}'}

        self.default_params = {'instruments': 'EUR_USD,USD_JPY'}

        self.account_endpoint = 'https://api-fxpractice.oanda.com/v3/accounts'

        self.instruments_endpoint = 'https://api-fxpractice.oanda.com/v3/instruments'

        self.account_id = ''

    def getAllAccounts(self):

        response = requests.get(self.account_endpoint, headers=self.default_headers)
        return response.json()
    
    def setCurrentAccount(self, current_id):
        self.account_id = '/' + current_id

        response = requests.get(self.account_endpoint + self.account_id, headers= self.default_headers, params=self.default_params )

        response = response.json()
        if 'errorMessage' in response:
            raise Exception("You have entered the wrong account_id")

    def getAccountSummary(self):
        if self.account_id == '':
            print("Account ID has not been set.")
            return ''
        
        response = requests.get(self.account_endpoint + self.account_id + '/summary', headers=self.default_headers)
        return response.json()

    def getCandles(self, timeframe, count, currency_pair):
        # timeframe format: H5 (4 hours) S5(5 seconds)

        get_candles = self.instruments_endpoint + "/" + currency_pair + "/candles"

        params = {'granularity': timeframe, 'count': count}

        response = requests.get(get_candles, headers=self.default_headers, params=params)

        if 'errorMessage' in response:
            raise Exception("Something went wrong with retrieving candles.")

        return response.json()

    def placeBuyOrder(self, currency_pair, amount, stopLoss, takeProfit):
        
        data = {
        "order": {
            "units": amount,
            "instrument": currency_pair,
            "timeInForce": "FOK",
            "type": "MARKET",
            "positionFill": "DEFAULT"
            }
        }
    
        if takeProfit > 0:
            data["order"]["takeProfitOnFill"] = {"price": takeProfit}
            
        if stopLoss > 0:
            data["order"]["stopLossOnFill"] = {"price": stopLoss}


        response = requests.post(self.account_endpoint + self.account_id + '/orders', headers=self.default_headers, data=json.dumps(data) )

        if response.status_code != 201:
            raise Exception("Could not execute the buy order.")

        return response.json()


    def placeSellOrder(self, currency_pair, amount, stopLoss, takeProfit):
        data = {
        "order": {
            "units": (-amount),
            "instrument": currency_pair,
            "timeInForce": "FOK",
            "type": "MARKET",
            "positionFill": "DEFAULT"
            }
        }
    
        if takeProfit > 0:
            data["order"]["takeProfitOnFill"] = {"price": takeProfit}
            
        if stopLoss > 0:
            data["order"]["stopLossOnFill"] = {"price": stopLoss}


        response = requests.post(self.account_endpoint + self.account_id + '/orders', headers=self.default_headers, data=json.dumps(data) )

        if response.status_code != 201:
            raise Exception("Could not execute the sell order.")

        return response.json()


    def getAllOrders(self):
        endpoint = self.account_endpoint + self.account_id + '/orders'
        response = requests.get(endpoint, headers=self.default_headers)

        if response.status_code != 200:
            raise Exception("Could not fetch all orders.")

        return response.json()


    def getAllTrades(self):
        endpoint = self.account_endpoint + self.account_id + '/trades'
        response = requests.get(endpoint, headers=self.default_headers)

        if response.status_code != 200:
            raise Exception("Could not fetch all trades.")

        return response.json()
    
    def getAllTransactions(self):
        endpoint = self.account_endpoint + self.account_id + '/transactions'
        response = requests.get(endpoint, headers=self.default_headers)

        if response.status_code != 200:
            raise Exception("Could not fetch all transactions")

        return response.json()
    
    def getTransactionSince(self, id):
        # params = type: ORDER_FILL
        params = {'id': id,'type': 'ORDER_FILL' }

        endpoint = self.account_endpoint + self.account_id + '/transactions/sinceid'
        response = requests.get(endpoint, headers=self.default_headers, params=params)

        if response.status_code != 200:
            raise Exception("Could not fetch all transactions since " + id)

        return response.json()
    
        
oanda = Oanda(os.getenv("ACCESS_TOKEN"))


lastid = {}


if os.path.exists("lastid.json"):
            with open("lastid.json") as f:
                lastid = json.load(f)


oanda.setCurrentAccount('101-001-24797201-001')
transactions = oanda.getTransactionSince(lastid["id"])


workbook = openpyxl.load_workbook("Trade Tracker.xlsx")

sheet = workbook["Sheet1"]

balance = []


for i in range(len(transactions['transactions'])):
    pair = transactions['transactions'][i]['instrument']
    price = transactions['transactions'][i]['pl']

    price = float(price)

    if price > 0:
        sheet["A" + str(lastid["currentrow"])] = pair
        sheet["B" + str(lastid["currentrow"])] = "win"
        sheet["E" + str(lastid["currentrow"])] = price
        lastid["currentrow"] += 1
    elif price < 0:
        sheet["A" + str(lastid["currentrow"])] = pair
        sheet["C" + str(lastid["currentrow"])] = "lose"
        sheet["F" + str(lastid["currentrow"])] = abs(price)
        lastid["currentrow"] += 1
    # else:
    #     sheet["D" + str(lastid["currentrow"])] = "BE"

    # Balance of user 
    curbal = transactions['transactions'][i]['accountBalance']
    balance.append(curbal)
    sheet["H" + str(lastid["currentrow"])] = curbal
    sheet["I" + str(lastid["currentrow"])] = transactions['transactions'][i]['id']
    sheet["J" + str(lastid["currentrow"])] = transactions['transactions'][i]['time']


    
if transactions['transactions'] != []:
    lastid["id"] = transactions['transactions'][len(transactions['transactions']) -1]['id']
else:
    print("You are caught up!")

workbook.save("Trade Tracker.xlsx")

with open('lastid.json', 'w') as f:
        json.dump(lastid, f)








