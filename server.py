from flask import Flask, render_template, session, redirect, request, flash
import re #importing the regex module
from flask_bcrypt import Bcrypt
from mysqlconnection import connectToMySQL

app = Flask(__name__, template_folder="templates")
app.secret_key = "The secrest biz u ever seent"
bcrypt = Bcrypt(app)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
BIRTHDAY_REGEX = re.compile(r'^(19|20)\d\d[- /.](0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])$')

def login_user(user_info, session_object):
    session_object['curr_user_id'] = user_info['id']
    session_object['curr_user_name'] = user_info['name']

@app.route('/')
def show_login():
    print("*"*80)
    print("in the show_login function")
    return render_template ("login.html")

@app.route('/home')
def show_home():
    print("*"*80)
    print("in the show_home function")
    if not 'curr_user_id' in session:
        return redirect("/")
    else:
        logged_in_user = {
            'name': session['curr_user_name'],
            'id': session['curr_user_id'],
        }
        print(logged_in_user)
        print(logged_in_user['id'])
        print("*"*50)

        mysql = connectToMySQL("quotes")
        users_query = "SELECT * FROM users;"
        users = mysql.query_db(users_query)
        context = {
            'user': logged_in_user,
            'users': users,
        }

        mysql = connectToMySQL("quotes")
        quotes_query = "SELECT users.id, first_name, last_name, author, quote, quotes.id FROM users JOIN quotes ON quotes.user_id = users.id WHERE users.id != %(user_id)s;"
        data = {
            'user_id': session['curr_user_id'],
        }
        quotes = mysql.query_db(quotes_query, data)
        print(quotes)
        context2 = {
            'quotes' : quotes,
        }

        mysql = connectToMySQL("quotes")
        query = "SELECT users.id, first_name, last_name, author, quote, quotes.id FROM users JOIN quotes ON quotes.user_id = users.id WHERE users.id = %(user_id)s;"
        data = {
            'user_id': session['curr_user_id'],
        }
        results = mysql.query_db(query, data)
        print(results)
        context3 = {
            'quotes1': results
        }

        return render_template("home.html", context=context, context2=context2, context3=context3)

@app.route('/user/<user_id>')
def show_users_quotes(user_id):
    print("*"*80)
    print("in the show_user_quotes function")
    if not 'curr_user_id' in session:
        return redirect("/")
    else:
        logged_in_user = {
            'name': session['curr_user_name'],
            'id': session['curr_user_id']
        }
        print(logged_in_user)
        print(logged_in_user['id'])
        print("*"*50)

        mysql = connectToMySQL("quotes")
        uquotes_query = "SELECT * FROM users JOIN quotes ON quotes.user_id = users.id WHERE user_id = %(user_id)s;"
        data = {
            'user_id': user_id,
        }
        quotes = mysql.query_db(uquotes_query, data)
        print(quotes)
        context = {
            'quotes': quotes,
        }

        mysql = connectToMySQL("quotes")
        users_query = "SELECT * FROM users;"
        users = mysql.query_db(users_query)
        context2 = {
            'user': logged_in_user,
            'users': users,
        }
    return render_template("users_quotes.html", context=context, context2=context2)

@app.route('/myaccount/<user_id>')
def show_edit_account(user_id):
    print("*"*80)
    print("in the show_edit_account function")
    if not 'curr_user_id' in session:
        return redirect("/")

    else:
        logged_in_user = {
            'name': session['curr_user_name'],
            'id': session['curr_user_id']
        }
        print(logged_in_user)
        print(logged_in_user['id'])
        print("*"*50)
        # query to return values to populate edit account fields
        mysql = connectToMySQL("quotes")
        query = "SELECT * FROM users WHERE id = %(user_id)s;"
        data = {
            'user_id': user_id,
        }
        user = mysql.query_db(query, data)
        print(user)
        context = {
            'user': user,
        }
    return render_template("edit_account.html", context=context)

@app.route('/logout')
def logout():
    print("*"*80)
    print("logging out")
    session.clear()
    return redirect("/")

@app.route("/register", methods=["POST"])
def register():
    print("*"*80)
    print(request.form)
    error_messages = []
    # check validations
    if not request.form['first_name'].isalpha():
        error_messages.append("First name must be alphabetic characters!")
    if len(request.form['first_name']) < 2:
        error_messages.append("First name must be longer than two characters!")
    if len(request.form['last_name']) < 2:
        error_messages.append("Last name needs to be longer than two characters!")
    if not EMAIL_REGEX.match(request.form['email']): #test whether a field matches the email pattern
        error_messages.append("Email must follow format name@email.com")
    if request.form['password'] != request.form['confirm_password']:
        error_messages.append("Passwords don't match")
    if len(request.form['confirm_password']) < 2:
        error_messages.append("Passwords don't match")
    if len(request.form['password']) < 2:
        error_messages.append("Password must be longer than two characters")

    if len(error_messages) == 0:
        # log our user in...
        pw_hash = bcrypt.generate_password_hash(request.form['password']) #creates a password hash
        mysql = connectToMySQL("quotes")
        query = "INSERT INTO users (first_name, last_name, email, password_hash, created_at, updated_at) VALUES (%(first)s, %(last)s, %(email)s, %(password)s, NOW(), NOW());"
        data = {
            'first': request.form['first_name'],
            'last': request.form['last_name'],
            'email': request.form['email'],
            'password': pw_hash,
        }
        results = mysql.query_db(query, data)
        print(results)
        login_user({'id': results, 'name': request.form['first_name']}, session)
        return redirect("/home")
    else:
        # flash a bunch of messages
        for message in error_messages:
            print(message)
            flash(message)
        return redirect("/")

@app.route("/login", methods= ['POST'])
def login():
    errors = []
    # grab deetz
    input_pw = request.form['password']
    input_email = request.form['email']
    # see if user exists
    mysql = connectToMySQL("quotes")
    query = "SELECT * FROM users WHERE(email = %(email)s)"
    data = {
        'email': input_email
    }
    result = mysql.query_db(query, data)
    if len(result) is not 1:
        errors.append("Email is incorrect!")
    else:
        if not bcrypt.check_password_hash(result[0]['password_hash'], input_pw):
            errors.append("Password is incorrect!")
        else:
            login_user({'id': result[0]['id'], 'name':result[0]['first_name']}, session)
            print(session)
    if len(errors) == 0:
        return redirect("/home")
    else:
        flash("Incorrect login")
        return redirect("/")

@app.route('/quote/add', methods=["POST"])
def add_quote():
    print("*"*80)
    print("in add_quote function")
    print(request.form)
    if not 'curr_user_id' in session:
        return redirect("/")
    error_messages = []

    if len(request.form['author']) < 3:
        error_messages.append("Author name must be longer than 3 characters!")
    if len(request.form['quote']) < 3:
        error_messages.append("Quote must be longer than 10 characters")

    if len(error_messages) == 0:
        logged_in_user = {
            'name': session['curr_user_name'],
            'id': session['curr_user_id'],
        }
        mysql = connectToMySQL("quotes")
        query = "INSERT INTO quotes (author, quote, created_at, updated_at, user_id) VALUES (%(auth)s, %(quote)s, NOW(), NOW(), %(user_id)s);"
        data = {
            'auth': request.form['author'],
            'quote': request.form['quote'],
            'user_id': session['curr_user_id'],
        }
        print(data)
        quote_results = mysql.query_db(query, data)
        print(quote_results)
        return redirect('/home')
    else:
        for message in error_messages:
            print(message)
            flash(message)
        return redirect("/home")

@app.route('/user/edit/<user_id>', methods=["POST"])
def edit_user(user_id):
    print("*"*80)
    print("in edit_user function")
    print(request.form)
    if not 'curr_user_id' in session:
        return redirect("/")

    else:
        error_messages = []
        if not request.form['first_name'].isalpha():
            error_messages.append("First name must be alphabetic characters!")
        if len(request.form['first_name']) < 2:
            error_messages.append("First name must be longer than two characters!")
        if len(request.form['last_name']) < 2:
            error_messages.append("Last name needs to be longer than two characters!")
        if not EMAIL_REGEX.match(request.form['email']): #test whether a field matches the email pattern
            error_messages.append("Email must follow format name@email.com")

        if len(error_messages) == 0:
            logged_in_user = {
                'name': session['curr_user_name'],
                'id': session['curr_user_id'],
            }
            mysql = connectToMySQL("quotes")
            query = "UPDATE users SET first_name = %(fname)s, last_name = %(lname)s, email = %(em)s WHERE id = %(user_id)s;"
            data = {
                "fname": request.form['first_name'],
                "lname": request.form['last_name'],
                "em": request.form['email'],
                "user_id": user_id,
            }
            print(data)
            results = mysql.query_db(query, data)
            print(results)
            return redirect('/home')
        else:
            for message in error_messages:
                print(message)
                flash(message)
            return redirect("/myaccount/"+user_id)

@app.route('/delete/<quote_id>', methods=["POST"])
def delete_quote(quote_id):
    print("*"*80)
    print("in delete_quote function")
    if not 'curr_user_id' in session:
        return redirect("/")
    else:
        logged_in_user = {
            'name': session['curr_user_name'],
            'id': session['curr_user_id']
        }
        print("*"*50)

        mysql = connectToMySQL("quotes")
        query = "DELETE FROM quotes WHERE id = %(quote_id)s;"
        data = {
            "quote_id": quote_id,
        }
        delete_quote = mysql.query_db(query, data)
        print(delete_quote)
        return redirect('/home')


if __name__=="__main__":
    app.run(debug=True)
