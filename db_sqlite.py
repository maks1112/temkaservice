import sqlite3
import ast
from datetime import datetime

DATABASE_PATH = 'db_market'
db_name = 'tg_market'
_action_catalog = 'action_catalog'
_action_buy = 'actions_buy'
_action_payment = 'action_payment'
_my_profile = 'my_profile'
_payment = 'payment'


def initialize_databases():
    conn = sqlite3.connect(f'{DATABASE_PATH}/{db_name}.db')
    cursor = conn.cursor()

    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {_action_catalog} (
        name TEXT,
        photo_path TEXT,
        text_path TEXT,
        text_caption TEXT,
        next_action TEXT,
        button_text TEXT,
        price TEXT
    )
    ''')

    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {_action_buy} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        photo_path TEXT,
        text_path TEXT,
        quantity INTEGER,
        price REAL,
        download_link TEXT
    )
    ''')

    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {_action_payment} (
        id INTEGER,
        payment_code TEXT,
        time REAL,
        price REAL,
        quantity INTEGER,
        name TEXT
    )
    ''')

    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {_my_profile} (
        id INTEGER,
        balance REAL,
        registrate TEXT,
        my_purchase TEXT
    )
    ''')

    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {_payment} (
        id INTEGER,
        invoice_id TEXT,
        pay_url TEXT
    )
''')
    conn.commit()
    conn.close()


initialize_databases()


def connection(name_db):
    def decorator(func):
        def wrapper(*args, **kwargs):
            with sqlite3.connect(f'{DATABASE_PATH}/{name_db}.db', check_same_thread=False) as con:
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                result = func(cur, *args, **kwargs)
                con.commit()
            return result

        return wrapper

    return decorator


@connection(db_name)
def add_to_db(cur, _id):
    data = cur.execute(f'SELECT * FROM {_my_profile} WHERE id=?', (_id,)).fetchone()
    if data is None:
        _time = datetime.now().strftime('%Y-%m-%d')
        cur.execute(f'''INSERT INTO {_my_profile} (id, balance, registrate, my_purchase) 
        VALUES (?, ?, ?,?)
        ''', (_id, 0, _time, '()'))


@connection(db_name)
def get_data_my_profile(cur, _id):
    return dict(cur.execute(f'SELECT * FROM {_my_profile} WHERE id=?', (_id,)).fetchone())


@connection(db_name)
def update_balance(cur, _id, price):
    balance = dict(cur.execute(f'SELECT balance FROM {_my_profile} WHERE id=?', (_id,)).fetchone())
    cur.execute(f'UPDATE {_my_profile} SET balance=? WHERE id=?', (balance['balance'] - price, _id,))


@connection(db_name)
def update_my_purchase(cur, _id, data):
    my_purchase = dict(cur.execute(f'SELECT my_purchase FROM {_my_profile} WHERE id=?', (_id,)).fetchone())[
        'my_purchase']
    my_purchase = my_purchase[:-1]
    my_purchase += "'" + data + "'" + ')' if my_purchase.count(',') else "'" + data + "',)"
    cur.execute(f'UPDATE {_my_profile} SET my_purchase=? WHERE id=?', (my_purchase, _id))


@connection(db_name)
def take_my_purchase(cur, _id):
    data = dict(cur.execute(f'SELECT my_purchase FROM {_my_profile} WHERE id=?', (_id,)).fetchone())
    my_purchase = data['my_purchase']
    try:
        return ast.literal_eval(my_purchase)
    except Exception as ex:
        print(ex)
        return False


@connection(db_name)
def take_action_catalog(cur, name):
    try:
        data = dict(cur.execute(f'SELECT * FROM {_action_catalog} WHERE name=?', (name,)).fetchone())
        for key, value in data.items():
            if value.startswith("(") and value.endswith(
                    ")"):
                try:
                    data[key] = ast.literal_eval(value)
                except ValueError:
                    pass
            elif key == 'price':
                try:
                    data[key] = float(value)
                except ValueError:
                    pass
            elif key == 'button_text' and data[key]:
                data[key] = ast.literal_eval(value)
        return data
    except:
        pass


@connection(db_name)
def take_action_buy(cur, name):
    try:
        return dict(cur.execute(f'SELECT * FROM {_action_buy} WHERE name=?', (name,)).fetchone())
    except:
        pass


@connection(db_name)
def update_quantity(cur, name, quantity):
    db_quantity = take_action_buy(name)['quantity']
    cur.execute(F'UPDATE {_action_buy} SET quantity = ? WHERE name = ?', (db_quantity - quantity, name))


@connection(db_name)
def enqueue_purchase(cur, _id, price, name, payment_code=None, time=None, quantity=1):
    data = get_data_purchase(_id)
    if not data and time is None:
        cur.execute(f'''INSERT INTO {_action_payment} (id, price, quantity, name) 
        VALUES (?, ?, ?,?)
        ''', (_id, price, quantity, name))
    elif data and time is None:
        cur.execute(f'''
                UPDATE {_action_payment} SET price = ?, quantity = ? WHERE id = ?''', (price, quantity, _id))
    else:
        cur.execute(f''' UPDATE {_action_payment} SET price = ?, quantity = ?, payment_code = ?, time = ? 
                WHERE id = ?''', (price, quantity, payment_code, time, _id))


@connection(db_name)
def get_data_purchase(cur, _id):
    try:
        return dict(cur.execute(f'SELECT * FROM {_action_payment} WHERE id=?', (_id,)).fetchone())
    except Exception as e:
        pass


@connection(db_name)
def delete_data_purchase(cur, _id):
    try:
        cur.execute(f'DELETE FROM {_action_payment} WHERE id=?', (_id,))
    except Exception as e:
        pass


@connection(db_name)
def update_purchase_quantity(cur, _id, quantity):
    cur.execute(f'''UPDATE {_action_payment} SET quantity = ? WHERE id = ?''', (quantity, _id))


@connection(db_name)
def add_action_catalog_data(cur, data):
    for action_name, action_data in data.items():
        photo_path = action_data.get('photo_path', '')
        text_path = action_data.get('text_path', '')
        text_caption = action_data.get('text_caption', '')
        button_text = str(action_data.get('buttons', ''))
        text_caption = str(text_caption)
        next_action = str(action_data.get('next_action', ''))
        price = action_data.get('price', 0)
        price = str(price)

        action_name = str(action_name)
        photo_path = str(photo_path)
        text_path = str(text_path)
        text_caption = str(text_caption)
        next_action = str(next_action)

        cur.execute('''
        INSERT INTO action_catalog (name, photo_path, text_path, text_caption, next_action, button_text, price) 
        VALUES (?, ?, ?, ?, ?, ?,?)
        ''', (action_name, photo_path, text_path, text_caption, next_action, button_text, price))


@connection(db_name)
def add_actions_buy_data(cur, data):
    for action_name, action_data in data.items():
        photo_path = action_data.get('photo_path', '')
        text_path = action_data.get('text_path', '')
        quantity = action_data.get('quantity', 0)
        price = action_data.get('price', 0)

        cur.execute('''
        INSERT INTO actions_buy (name, photo_path, text_path, quantity, price) 
        VALUES (?, ?, ?, ?, ?)
        ''', (action_name, photo_path, text_path, quantity, price))


@connection(db_name)
def add_data_payment(cur, _id, invoice_id, pay_url):
    cur.execute(f'''INSERT INTO {_payment} (id, invoice_id, pay_url) 
        VALUES (?, ?, ?)
        ''', (_id, invoice_id, pay_url))


@connection(db_name)
def get_data_payment(cur, _id):
    return dict(cur.execute(F'SELECT * FROM {_payment} WHERE id = ?', (_id,)).fetchone())


@connection(db_name)
def delete_data_payment(cur, _id):
    cur.execute(f'DELETE FROM {_payment} WHERE id=?', (_id,))
