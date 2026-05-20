from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
import boto3

app = Flask(__name__)

app.secret_key = 'foodorder123'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'foodapp'

mysql = MySQL(app)

bcrypt = Bcrypt(app)

@app.route('/')
def home():
    return "Food Ordering System Running"
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        role = "user"

        cur = mysql.connection.cursor()

        cur.execute(
            "INSERT INTO users(username,email,password,role) VALUES(%s,%s,%s,%s)",
            (username, email, hashed_password, role)
        )

        mysql.connection.commit()

        cur.close()

        return "User Registered Successfully"

    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM users WHERE email=%s", (email,))

        user = cur.fetchone()

        cur.close()

        if user:

            stored_password = user[3]

            if bcrypt.check_password_hash(stored_password, password):

                session['username'] = user[1]
                session['role'] = user[4]

                return redirect('/dashboard')

            else:
                return "Invalid Password"

        else:
            return "User Not Found"

    return render_template('login.html')
@app.route('/dashboard')
def dashboard():

    if 'username' in session:

        return render_template(
            'dashboard.html',
            username=session['username'],
            role=session['role']
        )

    return redirect('/login')
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')
@app.route('/addfood', methods=['GET', 'POST'])
def addfood():

    if request.method == 'POST':

        food_name = request.form['food_name']
        price = request.form['price']
        category = request.form['category']

        image = request.files['image']

        filename = image.filename

        bucket_name = 'foodapp-images-2026'

        s3.upload_fileobj(image, bucket_name, filename)

        image_url = f"https://{bucket_name}.s3.amazonaws.com/{filename}"

        cur = mysql.connection.cursor()

        cur.execute(
            "INSERT INTO foods(food_name,price,category,image_url) VALUES(%s,%s,%s,%s)",
            (food_name, price, category, image_url)
        )

        mysql.connection.commit()

        cur.close()

        return "Food Added Successfully"

    return render_template('addfood.html')
@app.route('/foods')
def foods():

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM foods")

    foods = cur.fetchall()

    cur.close()

    return render_template('foods.html', foods=foods)
@app.route('/deletefood/<int:id>')
def deletefood(id):

    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM foods WHERE id=%s", (id,))

    mysql.connection.commit()

    cur.close()

    return redirect('/foods')
@app.route('/editfood/<int:id>', methods=['GET', 'POST'])
def editfood(id):

    cur = mysql.connection.cursor()

    if request.method == 'POST':

        food_name = request.form['food_name']
        price = request.form['price']
        category = request.form['category']

        cur.execute(
            "UPDATE foods SET food_name=%s, price=%s, category=%s WHERE id=%s",
            (food_name, price, category, id)
        )

        mysql.connection.commit()

        cur.close()

        return redirect('/foods')

    cur.execute("SELECT * FROM foods WHERE id=%s", (id,))

    food = cur.fetchone()

    cur.close()

    return render_template('editfood.html', food=food)
@app.route('/addtocart/<int:id>')
def addtocart(id):

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM foods WHERE id=%s", (id,))

    food = cur.fetchone()

    cur.close()

    if 'cart' not in session:
        session['cart'] = []

    cart = session['cart']

    cart.append({
        'id': food[0],
        'food_name': food[1],
        'price': food[2]
    })

    session['cart'] = cart

    return redirect('/cart')
@app.route('/cart')
def cart():

    cart = session.get('cart', [])

    return render_template('cart.html', cart=cart)
@app.route('/removefromcart/<int:index>')
def removefromcart(index):

    cart = session.get('cart', [])

    if len(cart) > index:
        cart.pop(index)

    session['cart'] = cart

    return redirect('/cart')
@app.route('/placeorder')
def placeorder():

    cart = session.get('cart', [])

    username = session.get('username')

    if not cart:
        return "Cart is Empty"

    cur = mysql.connection.cursor()

    for item in cart:

        cur.execute(
            "INSERT INTO orders(username,food_name,price) VALUES(%s,%s,%s)",
            (username, item['food_name'], item['price'])
        )

    mysql.connection.commit()

    cur.close()

    session['cart'] = []

    return "Order Placed Successfully"

if __name__ == '__main__':
    app.run(debug=True)