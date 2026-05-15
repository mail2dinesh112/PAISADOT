# 🧾 SpendWise – Full Product PRD (Super Admin + Individual User)

---

# 🎯 PRODUCT OVERVIEW

SpendWise is a **multi-user expense tracking system** where:

* Super Admin manages accounts and users
* Users track expenses, budgets, and reports

---

# 👑 1. SUPER ADMIN FLOW

---

## 🔐 1.1 Login

### Purpose:

Super admin logs into admin panel

### Behavior:

* Email + password login
* On success → redirect to dashboard
* Invalid → error message

---

## 🏠 1.2 Dashboard

### Purpose:

Quick overview of system

### Show:

* Total accounts
* Total users
* Account type count:

  * Individual
  * Family
  * Group

---

---

# 🧩 1.3 Accounts Menu

## ➕ Create Account

### Fields:

* Account Name (text)
* Account Type (dropdown)

  * Individual
  * Family
  * Group

### Behavior:

* Click Create → account saved
* Must be unique name (optional validation)

---

## 📋 Accounts List

### Columns:

* Account Name
* Account Type
* Members Count
* Status (Active / Disabled)
* Created Date

---

## 🔍 Filters:

* Account Type dropdown
* Search (account name)

---

## ⚙️ Actions:

* View account
* Disable / Enable account
* Delete (optional)

---

## ⚠️ Rules:

* Disabled account → users cannot login
* Account must have at least 1 admin user

---

---

# 👥 1.4 Users Menu

## 📋 User List

### Columns:

* Name
* Email
* Phone
* Account Name
* Role (Admin / Member / Viewer)
* Status
* Created Date

---

## 🔍 Filters:

* Account dropdown
* Role dropdown
* Search (name/email)

---

## ➕ Add User

### Popup Fields:

* Account Name (dropdown)
* Role (Admin / Member / Viewer)
* Name
* Email
* Phone

---

### Behavior:

* User created and linked to account
* Email must be unique

---

## ⚙️ Actions:

* Edit user
* Disable / Enable
* Delete (optional)

---

## ⚠️ Rules:

* Each account must have at least 1 admin
* Cannot delete last admin

---

---

# 👤 2. INDIVIDUAL USER FLOW

---

## 🔐 2.1 Login

### Behavior:

* User login with email/password
* Redirect → Dashboard

---

---

# 🏠 2.2 Dashboard

## Purpose:

Quick overview of spending

---

## Show:

* Current month total expense
* Budget remaining
* Top 3 categories
* Recent 5 expenses

---

## Actions:

* “+ Add Expense” button

---

---

# 💸 2.3 Expenses Menu

---

## ➕ Add Expense

### Fields:

* Amount (mandatory)
* Category (mandatory)
* Date (mandatory)
* Payment Method (cash/UPI/card)
* Description (optional)
* Notes (optional)

---

### Category Handling:

* Dropdown with default categories
* If category not available:

  * “+ Add Category” option
  * Popup → create category
  * Auto-select after creation

---

### Behavior:

* Save → expense added
* Dashboard updated

---

---

## 📋 Expense List

### Columns:

* Date
* Category
* Amount
* Payment Method
* Description

---

## 🔍 Filters:

* Date range
* Category
* Payment method

---

## ⚙️ Actions:

* Edit expense
* Delete expense

---

---

# 💰 2.4 Budget Menu

---

## ➕ Set Budget

### Options:

* Monthly overall budget
* Category-wise budget

---

## 📊 Display:

* Used vs remaining
* Progress bar

---

## 🔔 Alerts:

* 80% usage warning
* Budget exceeded alert

---

---

# 📊 2.5 Reports Menu

---

## 📈 Charts:

### 1. Category Pie Chart

* Shows % split by category

---

### 2. Monthly Trend (Line Chart)

* Shows monthly spending trend

---

### 3. Budget vs Actual (Bar Chart)

* Compare planned vs actual

---

### 4. Daily/Weekly Bar Chart

* Shows short-term spending

---

---

## 🧠 Insights:

* “Spending increased by 20%”
* “Top category: Food”
* “Highest spending day: Sunday”

---

## 🔍 Filters:

* Date range
* Category

---

---

# ⚙️ 2.6 Settings

---

## 👤 Profile:

* Update name, phone

---

## 📂 Categories:

* Add / edit / delete custom categories

---

## 🔁 Recurring Expenses:

* Add recurring monthly expenses

---

## 🔔 Preferences:

* Enable/disable notifications

---

---

# ⚠️ GLOBAL RULES

---

## 🔐 Access Control:

* User can access only their account data

---

## 🧠 Data Integrity:

* No negative amounts
* No orphan accounts
* At least one admin per account

---

## 🔄 Updates:

* Editing expense updates reports instantly

---

---

# 🚀 MVP SCOPE

---

## Phase 1:

* Login
* Account creation
* Expense CRUD
* Dashboard

---

## Phase 2:

* Budget
* Reports

---

## Phase 3:

* Recurring
* Insights

---

# 🎯 FINAL SUMMARY

* Super Admin → manages accounts & users
* User → tracks expenses
* Dashboard → quick view
* Reports → deep analysis

---
