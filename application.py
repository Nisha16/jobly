from flask import Flask,render_template, request, url_for, redirect, flash, session
from dbConnect import connection
import gc

from wtforms import Form, BooleanField, IntegerField, TextField, validators, PasswordField
from passlib.hash import sha256_crypt

from MySQLdb import escape_string as thwart

app = Flask(__name__)

@app.route('/', methods=["GET","POST"])
def main():
	error = ''
	try:
		c, conn = connection()
		if request.method == "POST":
			data = c.execute("SELECT * FROM User WHERE email = (%s)", thwart(request.form['email']))
			data = c.fetchone()[4]
			print "data: ", data

			if sha256_crypt.verify(request.form['password'], data):
				print "Member signed in"
				session['logged_in'] = True
				session['email'] = request.form['email']

				flash("You are now logged in")
				return redirect(url_for("homepage"))
			else:
				error = "Invalid credentials, Please try again."

		gc.collect()
		return render_template("index.html", error=error)

	except Exception as e:
		error = "Record does not exists."
		# flash(e)
		return render_template('index.html', error=error)

@app.route('/homepage/')
def homepage():
	return render_template("homepage.html")


class RegistrationForm(Form):
	firstname = TextField('Firstname', [validators.Length(min=2, max=20)])
	lastname = TextField('Lastname', [validators.Length(min=2, max=20)])
	email = TextField('Email Address', [validators.Length(min=6, max=50)])
	password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
	confirm = PasswordField('Repeat Password')
	accept_tos = BooleanField('I accept the Terms of Service and Privacy Notice (updated Jan 21, 2017)', [validators.Required()])

@app.route('/register/', methods=["GET","POST"])
def register_page():
	try:
		form = RegistrationForm(request.form)

		if request.method == "POST" and form.validate():
			firstname = form.firstname.data
			lastname = form.lastname.data
			email = form.email.data
			password = sha256_crypt.encrypt((str(form.password.data)))
			c, conn = connection()

			x = c.execute("SELECT * FROM User WHERE email = (%s)", (thwart(email)))
			if int((x)) > 0:
				print "Member exists"
				flash("Email already registered. Try signing In")
				return render_template('register.html', form=form)
			else:
				c.execute("INSERT INTO User (firstname, lastname, email, password) VALUES (%s, %s, %s, %s)",
				(thwart(firstname), thwart(lastname), thwart(email), thwart(password)))
				conn.commit()
				print "New member"
				flash("Thanks for registering.")
				c.close()
				conn.close()
				gc.collect()
				session['logged_in'] = True
				session['firstname'] = firstname

				return redirect(url_for('homepage'))
		return render_template("register.html", form=form)
	except Exception as e:
		return (str(e))
@app.errorhandler(405)
def page_not_found(e):
	return render_template('405.html')

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html')

app.secret_key = "\x18\x98\\\xfdj#\x83JYh7\x84"

if __name__ == "__main__":
	app.debug = True
	app.run()
