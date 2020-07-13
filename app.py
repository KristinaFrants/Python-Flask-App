from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt


app = Flask(__name__)


#config mysql
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Passtwofish'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/articles')
def articles():
    return render_template('articles.html', articles= Articles)

@app.route('/article/<string:id>')
def article(id):
    return render_template('article.html', id=id)

class RegisterForm(Form):
    name = StringField('First Name', [validators.Length(max=50)])
    username  = StringField('Username', [validators.Length(max=50)])
    email  = StringField('email', [validators.Length(min=6, max=50), validators.DataRequired() ])
    password  = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message="Password do not match")
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #create cursor (cursor- allows to interact to DB execute the statement and return it back)
        cur = mysql.connection.cursor()
        #execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
        #connect to DB
        mysql.connection.commit()
        #close connection
        cur.close()
        flash('You are registered', 'success')

        redirect(url_for('home'))
    return render_template('register.html', form=form)



if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug= True)