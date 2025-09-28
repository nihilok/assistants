User:
Give me examples of "code smells" in Python.

Assistant:
Here are common code smells in Python with examples and better alternatives:

## 1. **Long Functions/Methods**

**Bad:**
```python
def process_user_data(user_data):
    # 50+ lines of validation, processing, formatting, saving, etc.
    if not user_data.get('email'):
        raise ValueError("Email required")
    if '@' not in user_data['email']:
        raise ValueError("Invalid email")
    # ... many more lines
    formatted_name = user_data['name'].title()
    # ... database operations
    # ... email sending
    # ... logging
```

**Better:**
```python
def process_user_data(user_data):
    validate_user_data(user_data)
    formatted_data = format_user_data(user_data)
    save_user(formatted_data)
    send_welcome_email(formatted_data['email'])
    log_user_creation(formatted_data['id'])
```

## 2. **Duplicate Code**

**Bad:**
```python
def calculate_employee_bonus(employee):
    if employee.department == 'sales':
        base_salary = employee.salary
        years_worked = employee.years_of_service
        bonus = base_salary * 0.1 + years_worked * 1000
        return bonus
    elif employee.department == 'engineering':
        base_salary = employee.salary
        years_worked = employee.years_of_service
        bonus = base_salary * 0.15 + years_worked * 1500
        return bonus
```

**Better:**
```python
def calculate_employee_bonus(employee):
    bonus_rates = {
        'sales': (0.1, 1000),
        'engineering': (0.15, 1500)
    }
    
    rate, yearly_bonus = bonus_rates.get(employee.department, (0, 0))
    return employee.salary * rate + employee.years_of_service * yearly_bonus
```

## 3. **Long Parameter Lists**

**Bad:**
```python
def create_user(first_name, last_name, email, phone, address, city, 
                state, zip_code, country, age, gender, occupation):
    # function body
```

**Better:**
```python
from dataclasses import dataclass

@dataclass
class UserData:
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str
    city: str
    state: str
    zip_code: str
    country: str
    age: int
    gender: str
    occupation: str

def create_user(user_data: UserData):
    # function body
```

## 4. **Magic Numbers/Strings**

**Bad:**
```python
def calculate_tax(income):
    if income < 50000:
        return income * 0.1
    elif income < 100000:
        return income * 0.2
    else:
        return income * 0.3
```

**Better:**
```python
# Constants at module level
TAX_BRACKETS = [
    (50000, 0.1),
    (100000, 0.2),
    (float('inf'), 0.3)
]

def calculate_tax(income):
    for bracket_limit, rate in TAX_BRACKETS:
        if income < bracket_limit:
            return income * rate
```

## 5. **Deeply Nested Code**

**Bad:**
```python
def process_orders(orders):
    results = []
    for order in orders:
        if order.is_valid():
            if order.customer.is_active():
                if order.total > 0:
                    if order.payment_method:
                        # actual processing
                        results.append(process_single_order(order))
    return results
```

**Better:**
```python
def process_orders(orders):
    results = []
    for order in orders:
        if not should_process_order(order):
            continue
        results.append(process_single_order(order))
    return results

def should_process_order(order):
    return (order.is_valid() and 
            order.customer.is_active() and 
            order.total > 0 and 
            order.payment_method)
```

## 6. **Large Classes**

**Bad:**
```python
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.orders = []
    
    # User management methods
    def update_profile(self): pass
    def change_password(self): pass
    
    # Order management methods
    def create_order(self): pass
    def cancel_order(self): pass
    def get_order_history(self): pass
    
    # Payment methods
    def process_payment(self): pass
    def refund_payment(self): pass
    
    # Email methods
    def send_welcome_email(self): pass
    def send_order_confirmation(self): pass
```

**Better:**
```python
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email

class OrderManager:
    def __init__(self, user):
        self.user = user
    
    def create_order(self): pass
    def cancel_order(self): pass

class PaymentProcessor:
    def process_payment(self, user, amount): pass
    def refund_payment(self, user, amount): pass

class EmailService:
    def send_welcome_email(self, user): pass
    def send_order_confirmation(self, user, order): pass
```

## 7. **Inappropriate Comments**

**Bad:**
```python
# Increment i by 1
i += 1

# Check if user is None
if user is None:
    return

def calculate_area(radius):
    # Use pi times radius squared
    return 3.14159 * radius * radius
```

**Better:**
```python
i += 1  # No comment needed

if user is None:
    return  # No comment needed

def calculate_area(radius):
    """Calculate the area of a circle given its radius."""
    return math.pi * radius ** 2
```

## 8. **Feature Envy**

**Bad:**
```python
class Invoice:
    def calculate_total(self, customer):
        # This method knows too much about Customer internals
        discount = 0
        if customer.membership_years > 5:
            discount = 0.1
        elif customer.membership_years > 2:
            discount = 0.05
        
        return self.subtotal * (1 - discount)
```

**Better:**
```python
class Customer:
    def get_discount_rate(self):
        if self.membership_years > 5:
            return 0.1
        elif self.membership_years > 2:
            return 0.05
        return 0

class Invoice:
    def calculate_total(self, customer):
        discount_rate = customer.get_discount_rate()
        return self.subtotal * (1 - discount_rate)
```

## 9. **Mutable Default Arguments**

**Bad:**
```python
def add_item(item, target_list=[]):
    target_list.append(item)
    return target_list
```

**Better:**
```python
def add_item(item, target_list=None):
    if target_list is None:
        target_list = []
    target_list.append(item)
    return target_list
```

## 10. **God Object/Class**

**Bad:**
```python
class GameEngine:
    def __init__(self):
        # Handles everything: graphics, sound, input, AI, physics, etc.
        pass
    
    def render_graphics(self): pass
    def play_sound(self): pass
    def handle_input(self): pass
    def update_ai(self): pass
    def calculate_physics(self): pass
    def manage_database(self): pass
    def handle_networking(self): pass
```

**Better:**
```python
class GraphicsRenderer: pass
class SoundManager: pass
class InputHandler: pass
class AIManager: pass
class PhysicsEngine: pass
class DatabaseManager: pass
class NetworkManager: pass

class GameEngine:
    def __init__(self):
        self.graphics = GraphicsRenderer()
        self.sound = SoundManager()
        self.input = InputHandler()
        # ... etc
```

These code smells indicate areas where code could be refactored for better maintainability, readability, and extensibility.
