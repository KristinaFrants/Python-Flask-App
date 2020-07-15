from flask import Flask, render_template, flash, redirect, url_for, session, logging, request 
# from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)


#config mysql
app.config['MYSQL_HOST'] = os.environ.get('DB_HOST')
app.config['MYSQL_USER'] = os.environ.get('DB_USERNAME')
app.config['MYSQL_PASSWORD'] = os.environ.get('DB_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('DB_DBNAME')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/articles')
def articles():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    print(articles)

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = "No Articles Found" 
        return render_template('articles.html', msg=msg)
    cur.close()

@app.route('/article/<string:id>')
def article(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles WHERE id=%s", [id])
    article = cur.fetchone()
    return render_template('article.html', article=article)

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

        return redirect(url_for('dashboard'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        if result > 0:
            data = cur.fetchone()
            password = data['password']
            if sha256_crypt.verify(password_candidate, password):
                #Passed
                session['logged_in'] = True
                session['username'] = username

                flash("you are now logged in", 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
    return render_template('login.html')    

#check if user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('you are now logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = "No Articles Found" 
        return render_template('dashboard.html', msg=msg)
    cur.close()

#article form class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(max=200)])
    body  = TextAreaField('Body', [validators.Length(min=30)])


@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #create a cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username'])) 
        mysql.connection.commit()
        cur.close()
        flash('Article created', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)


@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    cur = mysql.connection.cursor()
    #get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()
    #get form
    form = ArticleForm(request.form)
    #populate article fields
    form.title.data = article['title']
    form.body.data = article['body']
    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']
        #create a cursor
        cur = mysql.connection.cursor()
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id = %s", (title, body, id)) 
        mysql.connection.commit()
        cur.close()
        flash('Article Updated', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html', form=form)

#Delete article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM articles WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    flash('Article Deleted', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug= True)