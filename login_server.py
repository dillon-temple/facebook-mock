import re
from flask import Flask, render_template, request, redirect, session, flash
from flask_bcrypt import Bcrypt
from serverSQL import connectToMySQL
app = Flask(__name__)
app.secret_key = "bobbyhill"
bcrypt = Bcrypt(app)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')


@app.route("/")
def index():


    return render_template("index.html")

@app.route("/add_user", methods=["POST"])
def add_user():

    fn = request.form["first_name"]
    ln = request.form["last_name"]
    em = request.form["email"]
    pass_en = bcrypt.generate_password_hash(request.form["pass"])

    pw = request.form["pass"]
    cpw = request.form["cpass"]
    is_valid = True

    validate = connectToMySQL("private_wall")
    query = f'SELECT email FROM users WHERE email = "{em}"'
    validate = validate.query_db(query)
    print(validate)

    if len(fn) < 2 or len(ln) < 2 or fn.isalpha() == False or ln.isalpha() == False:
        is_valid = False
        flash("Enter a valid name")
    if not EMAIL_REGEX.match(em):
        is_valid = False
        flash("Email is not valid")
    if validate:
        is_valid = False
        flash("Email already in use")
    if pw != cpw:
        is_valid = False
        flash("Passwords do not match")
    if len(pw) < 8:
        is_valid = False
        flash("Your password must be at least 8 characters long")

    if is_valid:
        user = connectToMySQL("private_wall")
        query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (%(fname)s,%(lname)s,%(em)s,%(pass)s,NOW(),NOW())"
        data = {
            "fname":fn,
            "lname":ln,
            "em":em,
            "pass":pass_en
        }
        update_db = user.query_db(query,data)
        flash("User Successfully Added!")
        return redirect("/")
    return redirect("/")

@app.route("/login", methods=["POST"])
def login_check():
    user = connectToMySQL("private_wall")
    query = 'SELECT * FROM users WHERE email = %(em)s'
    data = {
        "em": request.form["email"]
    }
    
    user = user.query_db(query,data)

    if user:
        if bcrypt.check_password_hash(user[0]["password"], request.form["pass"]):
            session["userid"] = user[0]["id"]
            session["useremail"] = user[0]["email"]
            session["first_name"] = user[0]["first_name"]
            print(session["userid"])
            return redirect('/success')
    flash("Login Failed")
    return redirect("/")



@app.route("/success")
def success():

    if "userid" in session:

        users = connectToMySQL("private_wall")
        query = "SELECT id, first_name FROM users WHERE NOT id = %(id)s"
        data = {
            "id":session["userid"]
        }
        users = users.query_db(query,data)
        print(users)

        messages = connectToMySQL("private_wall")
        query = "SELECT recipients.first_name, senders.first_name, messages.content, messages.id, messages.created_at \
                FROM users AS senders \
                LEFT JOIN messages \
                ON senders.id = messages.sender_id \
                LEFT JOIN users AS recipients \
                ON recipients.id = messages.recipient_id \
                WHERE recipients.id = %(current_user)s"

        data = {
            "current_user":session["userid"]
        }

        messages = messages.query_db(query,data)
        message_amount = len(messages)

        messages_sent = connectToMySQL("private_wall")
        query = "SELECT id FROM messages WHERE sender_id = %(current_user)s"
        data = {
            "current_user":session["userid"]
        }
        messages_sent = messages_sent.query_db(query,data)
        message_amount2 = len(messages_sent)

        return render_template("wall.html", users=users, messages=messages, count=message_amount, sent=message_amount2)
    else:
        return redirect("/")

@app.route("/send_message", methods=["POST"])
def send_message():

    print(len(request.form["message"]))
    is_valid = True

    if int(len(request.form["message"])) < 5:
        is_valid = False
        flash("Your message is too short!")
    if is_valid:
        message = connectToMySQL("private_wall")

        query = "INSERT INTO messages (sender_id, recipient_id, content, created_at, updated_at) VALUES (%(send)s,%(get)s,%(msg)s, NOW(), NOW());"
        data = {
            "send":session["userid"],
            "get":request.form["recipient_id"],
            "msg":request.form["message"]
        }
        message = message.query_db(query, data)

    return redirect("success")

@app.route("/delete/<id>")
def delete(id):

    delete = connectToMySQL("private_wall")
    query = "DELETE FROM messages WHERE messages.id = %(id)s"
    data = {
        "id":id
    }

    delete = delete.query_db(query, data)

    return redirect("/success")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")








if __name__ == "__main__":
    app.run(debug=True)
