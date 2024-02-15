import sqlite3
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime

# Create an SQLite database and a 'accounts' table
conn = sqlite3.connect('bank_database.db')
cursor = conn.cursor()
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
            print("Withdrawal failed. Insufficient funds.")
            return False

class CurrentAcc(Account):
    def withdraw(self, amount):
        if self.balance + self.overDraftLimit >= amount:
            self.balance -= amount
            return True
        else:
            print("Withdrawal failed. Overdraft limit reached.")
            return False

class Bank:
    @staticmethod
    def create_account(accNum, accHolder, accType, username, password):
        birthdate = accHolder.DoB
        today = datetime.now().date()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        if age < 15:
            print("Account creation failed. Customer must be 15 years or older.")
            return

        if accType == 'Savings':
            account = SavingsAcc(accNum, 0, accHolder, accType)
        elif accType == 'Current':
            account = CurrentAcc(accNum, 0, accHolder, accType)
        else:
            print("Invalid account type.")
            return

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute('SELECT * FROM accounts WHERE username=?', (username,))
        if cursor.fetchone():
            print("Username already exists. Choose a different one.")
            return

        account.save_to_database()
        print(f"Account created successfully for {accHolder.personName}.")
        print(f"Account Number: {accNum}")
        print(f"Username: {username}")

# Example usage:
person1 = Person("John Doe", "01-01-2005", "1234567890")
bank = Bank()
bank.create_account("123", person1, "Savings", "john_doe", "secure_password")