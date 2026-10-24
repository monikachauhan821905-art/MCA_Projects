# NexBank — Banking System (Flask)
## Experiment 3 · Unit 2 · CO3 — Inheritance & Polymorphism

---

## Setup & Run

```bash
# 1. Install Flask
pip install flask

# 2. Run
python app.py

# 3. Open browser
http://localhost:5000
```

---

## Team Division

| Person | Task |
|--------|------|
| **Person 1** | `BankAccount` (ABC), `SavingsAccount`, `CheckingAccount`, all business logic in `app.py` |
| **Person 2** | Flask routes (`/api/*`), HTML/CSS/JS frontend in `templates/index.html` |

---

## OOP Concepts Demonstrated

| Concept | Where |
|---------|-------|
| Abstract Base Class | `BankAccount(ABC)` — cannot instantiate directly |
| Inheritance | `SavingsAccount(BankAccount)`, `CheckingAccount(BankAccount)` |
| Polymorphism | `list[BankAccount]` in `/api/poly-demo` — calls `withdraw()` on each via base class reference |
| Encapsulation | `_balance` private, accessed only via methods |
| Method Overriding | `withdraw()` behaves differently per subclass |

---

## Features

- ✅ Create Savings (min ₹1,000) or Checking (overdraft ₹500) accounts  
- ✅ Deposit & Withdraw with validation  
- ✅ Quick amount buttons (₹500, ₹1000, ₹2000, ₹5000)  
- ✅ Real-time transaction history with timestamps  
- ✅ Polymorphism demo modal — runs on all accounts simultaneously  
- ✅ Toast notifications for every action  
- ✅ Dark premium UI  
