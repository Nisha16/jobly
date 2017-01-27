from flask import Flask,render_template
from dbConnect import connection

from wtforms import Form, BooleanField, IntegerField, TextField, validators, PasswordField
app = Flask(__name__)

@app.route('/')
def main():
	return render_template('index.html')


# class RegistrationForm(Form):
#     firstname = TextField('Firstname', [validators.Length(min=2, max=20)])
# 	lastname = TextField('Lastname', [validators.Length(min=2, max=20)])
#     phone = IntegerField('Phone', [validators.NumberRange(min=0, max=10)])
#     email = TextField('Email Address', [validators.Length(min=6, max=50)])
#     password = PasswordField('New Password', [
#         validators.Required(),
#         validators.EqualTo('confirm', message='Passwords must match')
#     ])
#     confirm = PasswordField('Repeat Password')
#     accept_tos = BooleanField('I accept the Terms of Service and Privacy Notice (updated Jan 21, 2017)', [validators.Required()])

# @app.route('/register/', methods=["GET","POST"])
# def register_page():
# 	try:
# 		c, conn = connection()
#         form = RegistrationForm(request.form)
#         if request.method == 'POST' and form.validate():
#             user = User(form.username.data, form.email.data,form.password.data)
#
# 		return ("OKAY")
# 	except Exception as e:
# 		return (str(e))

if __name__ == "__main__":
	app.run()
