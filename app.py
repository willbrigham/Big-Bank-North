from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime

app = Flask(__name__)

# SQLite database initialization
conn = sqlite3.connect('bank_database.db', check_same_thread=False)
cursor = conn.cursor()

# Create an SQLite database and a 'accounts' table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        accNum TEXT PRIMARY KEY,
        balance REAL,
        accHolderName TEXT,
        username TEXT,
        password TEXT,
        minBalance REAL,
        overDraftLimit REAL,
        accType TEXT,
        birthdate TEXT
    )
''')
conn.commit()

class Person:
    def __init__(self, personName, DoB, contactNo):
        self.personName = personName
        self.DoB = datetime.strptime(DoB, "%d-%m-%Y").date()
        self.contactNo = contactNo

class Account(ABC):
    def __init__(self, accNum, balance, accHolder, accType, minBalance=500, overDraftLimit=0):
        self.accNum = accNum
        self.balance = balance
        self.accHolder = accHolder
        self.accType = accType
        self.minBalance = minBalance
        self.overDraftLimit = overDraftLimit

    @abstractmethod
    def deposit(self, amount):
        pass

    @abstractmethod
    def withdraw(self, amount):
        pass

    def check_balance(self):
        return self.balance

    def save_to_database(self):
        birthdate_str = self.accHolder.DoB.strftime("%d-%m-%Y")
        cursor.execute('''
            INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.accNum, self.balance, self.accHolder.personName, self.accHolder.contactNo,
              self.accType, self.minBalance, self.overDraftLimit, self.accType, birthdate_str))
        conn.commit()

class SavingsAcc(Account):
    def deposit(self, amount):
        self.balance += amount

    def withdraw(self, amount):
        if self.balance - amount >= self.minBalance:
            self.balance -= amount
            return True
        else:
            return False

class CurrentAcc(Account):
    def withdraw(self, amount):
        if self.balance + self.overDraftLimit >= amount:
            self.balance -= amount
            return True
        else:
            return False

class Bank:
    @staticmethod
    def create_account(accNum, accHolder, accType, username, password):
        birthdate = accHolder.DoB
        today = datetime.now().date()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        if age < 15:
            return "Account creation failed. Customer must be 15 years or older."

        if accType == 'Savings':
            account = SavingsAcc(accNum, 0, accHolder, accType)
        elif accType == 'Current':
            account = CurrentAcc(accNum, 0, accHolder, accType)
        else:
            return "Invalid account type."

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute('SELECT * FROM accounts WHERE username=?', (username,))
        if cursor.fetchone():
            return "Username already exists. Choose a different one."

        account.save_to_database()
        return f"Account created successfully for {accHolder.personName}. Account Number: {accNum}"

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_account', methods=['POST'])
def create_account():
    accNum = request.form['accNum']
    personName = request.form['personName']
    DoB = request.form['DoB']
    contactNo = request.form['contactNo']
    accType = request.form['accType']
    username = request.form['username']
    password = request.form['password']

    accHolder = Person(personName, DoB, contactNo)
    bank = Bank()
    result = bank.create_account(accNum, accHolder, accType, username, password)

    return render_template('result.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
