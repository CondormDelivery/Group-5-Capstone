from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, login_required, logout_user
from flask_mail import Mail, Message
from passlib.hash import pbkdf2_sha256

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from forms import *

app = Flask(__name__)
#something crazy later
app.secret_key = 'meme'

ENV = 'prod'
if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Brad3nlive01@localhost/condorm'
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://kbqbgcqghvqwul:11d356f3b6f22a190cc58e471855f90f73bc107ae29a120e4dc245c224d8a024@ec2-52-87-107-83.compute-1.amazonaws.com:5432/davsklgj1tk9eo'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login = LoginManager(app)
login.init_app(app)

#app.config['MAIL_SERVER'] = 'smtp.gmail.com'
#app.config['MAIL_PORT'] = 587
#app.config['MAIL_USE_TLS'] = True
#app.config['MAIL_USERNAME'] = 'youremail@gmail.com'
#app.config['MAIL_PASSWORD'] = 'your_email_password'
#mail = Mail(app)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, unique=True, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    firstname = db.Column(db.String(), nullable=False)
    lastname = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    dormname = db.Column(db.String(), nullable=False)
    roomnum = db.Column(db.Integer(), nullable=False)
    admin = db.Column(db.Boolean(), nullable=False)
    children = relationship("Orders")

    def __init__(self, username, firstname, lastname, email, password, dormname, roomnum, admin):
        self.username = username
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.password = password
        self.dormname = dormname
        self.roomnum = roomnum
        self.admin = admin

class Orders(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, unique=True, primary_key=True)
    user_id = Column(db.Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="children")
    product_id = Column(db.Integer, ForeignKey('products.id'))
    quantity = db.Column(db.Integer, nullable = False)
    # This only includes the ID for a single product. We will implement expansions to that later.
    user = relationship("Products", back_populates="children")
    status = db.Column(db.Boolean(), nullable=False)

    def __init__(self, user_id, product_id, quantity, status):
        self.user_id = user_id
        self.product_id = product_id
        self.quantity = quantity
        self.status = status

class Products(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(200))
    quantity = db.Column(db.Integer)
    image = db.Column(db.String(100))
    children = relationship("Orders")

    def __init__(self, product, quantity, image):
        self.product = product
        self.quantity = quantity
        self.image = image


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/', methods = ['POST', 'GET'])
def index():
    return render_template('main.html')

@app.route('/login', methods = ['POST', 'GET'])
def mainpage():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user_object = User.query.filter_by(username=login_form.username.data).first()
        if not user_object:
            return render_template('login.html', form = login_form, message = "Incorrect username or password")
        if pbkdf2_sha256.verify(login_form.password.data, user_object.password): 
            login_user(user_object)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', form = login_form, message = "Incorrect username or password")
    return render_template('login.html', form = login_form)
    
 
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/order')
def order():
    if not current_user.is_authenticated:
        flash("Please login to place an order")
        return redirect(url_for('index'))
    products = Products.query.all()
    return render_template('order.html', products = products)

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        user_id = current_user.id
        product = request.form['products']
        quantity = int(request.form['quantity'])
        status = False

        if product == '' or quantity == '':
            return render_template('order.html', message = 'Please enter a valid product or quantity')

        prod_object = Products.query.filter_by(id = product).first()
        if prod_object.quantity >= quantity:
            prod_object.quantity = prod_object.quantity - quantity
            data = Orders(user_id, product, quantity, status)
            db.session.add(data)
            db.session.commit()
        else:
            flash("There is not enough inventory for that product. Try again!")
            return render_template('order.html')
        return render_template('submit.html')
    
@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/update', methods = ['GET', 'POST'])
def information():
    update_form = UpdateForm()
    if update_form.validate_on_submit():
        username = current_user.username
        dormname = update_form.dormname.data
        roomnum = update_form.roomnum.data
        user_object = User.query.filter_by(username = username).first()
        user_object.dormname = dormname
        user_object.roomnum = roomnum
        db.session.commit()
    return render_template('update.html', form = update_form)

@app.route('/registration', methods = ['GET', 'POST'])
def registration():

    reg_form = RegistrationForm()

    if reg_form.validate_on_submit():
        username = reg_form.username.data
        firstname = reg_form.firstname.data
        lastname = reg_form.lastname.data
        email = reg_form.email.data
        password = reg_form.password.data
        dormname = reg_form.dormname.data
        roomnum = reg_form.roomnum.data
        admin = False

        password_hashed = pbkdf2_sha256.hash(password)

        user_object = User.query.filter_by(username= username).first()
        email_object = User.query.filter_by(email = email).first()

        if user_object:
            return render_template('registration.html', form = reg_form, message = "Someone has taken that username!")
        if email_object:
            return render_template('registration.html', form = reg_form, message = "Someone has taken that email!")
        #msg = Message("Hello", sender= "no-reply@condormdelivery.com", recipients= [email])
        #mail.send(msg)
        user = User(username = username,firstname = firstname, lastname = lastname, email = email, password = password_hashed, dormname = dormname, roomnum = roomnum, admin = admin)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('mainpage'))
    return render_template('registration.html', form = reg_form)

@app.route("/admin", methods = ['GET', 'POST'])
def admin():
    if not current_user.is_authenticated:
        flash("Please login to access page.")
        return redirect(url_for('index'))
    if current_user.admin == False:
        flash("You don't have access to this page.")
        
    return render_template('admin.html')

@app.route("/orderlist", methods = ['GET', 'POST'])
def orderlist():
    #if current_user.admin == False:
        #return str(current_user.admin) #ERROR MESSAGE + ADD LOGIN REQUIREMENT#
    if not current_user.is_authenticated:
        flash("Please login to access page.")
        return redirect(url_for('index'))
    if current_user.admin == False:
        flash("You don't have access to this page.")

    if request.method == "POST":
        orderid = request.form['ordern']
        order_object = Orders.query.filter_by(id = orderid).first()
        order_object.status = True
        db.session.commit()

    orders = Orders.query.all()
    return render_template('orderlist.html', orders = orders)

@app.route("/products", methods = ['GET', 'POST'])
def products():
    #if current_user.admin == False:
        #return str(current_user.admin) #ERROR MESSAGE + ADD LOGIN REQUIREMENT#
    if not current_user.is_authenticated:
        flash("Please login to access page.")
        return redirect(url_for('index'))
    if current_user.admin == False:
        flash("You don't have access to this page.")

    if request.method == 'POST':
        productid = request.form['productn']
        product_object = Products.query.filter_by(id = productid).first()
        db.session.delete(product_object)
        db.session.commit()

    products = Products.query.all()
    return render_template('products.html', products = products)

@app.route("/users", methods = ['GET', 'POST'])
def users():
    #if current_user.admin == False:
        #return str(current_user.admin) #ERROR MESSAGE + ADD LOGIN REQUIREMENT#
    if not current_user.is_authenticated:
        flash("Please login to access page.")
        return redirect(url_for('index'))
    if current_user.admin == False:
        flash("You don't have access to this page.")

    if request.method == 'POST':
        userid = request.form['usern']
        user_object = User.query.filter_by(id = userid).first()
        user_object.admin = True
        db.session.commit()

    users = User.query.all()
    return render_template('users.html', users = users)

@app.route("/new_product", methods = ['GET', 'POST'])
def new_product():
    if not current_user.is_authenticated:
        flash("Please login to access page.")
        return redirect(url_for('index'))
    if current_user.admin == False:
        flash("You don't have access to this page.")
        
    new_productform = ProductForm()
    if new_productform.validate_on_submit():
        product = new_productform.productname.data
        quantity = new_productform.quantity.data
        image = new_productform.image.data

        item = Products(product, quantity, image)
        db.session.add(item)
        db.session.commit()
        return redirect(url_for('products'))
    return render_template('new_product.html', form = new_productform)

@app.route("/logout", methods = ["GET"])
def logout():
    logout_user()
    return render_template('main.html')
    
if __name__ == "__main__":
    app.run()
    
