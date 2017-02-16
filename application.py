from flask import Flask,render_template, request, url_for, redirect, flash, session
from dbConnect import connection
import gc
import os

from wtforms import Form, BooleanField, IntegerField, TextField, validators, PasswordField, DateField, TextAreaField
from flask_wtf.file import FileField, FileRequired
from wtforms.fields.html5 import DateField
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import timedelta
from werkzeug import secure_filename

from MySQLdb import escape_string as thwart

app = Flask(__name__)

# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'resumes/'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'doc', 'docx'])


@app.errorhandler(405)
def page_not_found(e):
	return render_template('405.html')

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html')

def login_required(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash("You need to log in first")
			return redirect(url_for('main'))
	return wrap

# Below functions to display contents for recruiters
@app.route('/', methods=["GET","POST"])
def main():
	error = ''
	try:
		c, conn = connection()
		if request.method == "POST":
			data = c.execute("SELECT * FROM User WHERE email = (%s)", thwart(request.form['email']))
			data = c.fetchall()
			print "data: ", data[0][4]

			if sha256_crypt.verify(request.form['password'], data[0][4]):
				print "Member signed in"
				session['logged_in'] = True
				session['email'] = request.form['email']
				flash("You are now logged in")
				jobList = None
				jobList = c.execute("SELECT * FROM Jobs WHERE creator = (%s)", session['email'])
				if int(jobList) > 0:
					jobList = c.fetchall()
					return render_template("homepage.html", data=data, jobList=jobList)
				else:
					return render_template("homepage.html", data=data)
			else:
				error = "Invalid credentials, Please try again."

		gc.collect()
		return render_template("index.html", error=error)

	except Exception as e:
		error = "Record does not exists."
		flash(e)
		return render_template('index.html', error=error)

@app.route('/logout/')
@login_required
def logout():
	session.clear()
	flash("You have been logged out!")
	gc.collect()
	return redirect(url_for('main'))

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
	# accept_tos = BooleanField('I accept the Terms of Service and Privacy Notice (updated Jan 21, 2017)', [validators.Required()])

class JobForm(Form):
	title = TextField('Title', [validators.Length(min=2, max=20)])
	requirement = TextAreaField('Requirement', [validators.Length(min=2, max=1000)])
	jobDesc = TextAreaField('Job Description', [validators.Length(min=2, max=1000)])
	location = TextField('Location', [validators.Length(min=2, max=20)])
	experience = IntegerField('Experience')
	rcg = BooleanField('RCG', default=False)
	internship = BooleanField('Internship', default=False)
	requisition = TextField('Req Number', [validators.Length(min=3, max=10)])
	reqdate = DateField('Req Date', format='%Y-%m-%d')
	dept = TextField('Department', [validators.Length(min=6, max=50)])

class ApplicantForm(Form):
	applicantName = TextField('Applicant Name', [validators.Length(min=2, max=20)])
	applicantEmail = TextField('Applicant Email Address', [validators.Length(min=6, max=50)])
	appliedDate = DateField('Applied Date', format='%Y-%m-%d')


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

@app.route('/add-new-job/', methods=["GET","POST"])
@login_required
def createJobRequisition():
	try:
		form = JobForm(request.form)
		print "Job email: ", session['email']
		if request.method == "POST" and form.validate():
			title = form.title.data
			requirement = form.requirement.data
			jobDesc = form.jobDesc.data
			location = form.location.data
			experience = form.experience.data
			rcg = form.rcg.data
			internship = form.internship.data
			requisition = form.requisition.data
			reqdate = form.reqdate.data
			dept = form.dept.data
			creator = session['email']
			c, conn = connection()

			x = c.execute("SELECT * FROM Jobs WHERE requisitionNumber = (%s)", (thwart(requisition)))
			if int((x)) > 0:
				print "Job exists"
				flash("Corresponding job requisition number already exists.")
				return render_template('newJob.html', form=form)
			else:
				c.execute("INSERT INTO Jobs (title, requirement, jobDesc, location, experience, RCG, internship, requisitionNumber, reqDate, dept, creator) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (title, requirement, jobDesc, location, experience, rcg, internship, requisition, reqdate, dept, creator))
				conn.commit()
				print "New Job added"
				flash("Job created successfully.")

				# Display added job
				jobList = None
				jobList = c.execute("SELECT * FROM Jobs WHERE creator = (%s)", session['email'])
				if int(jobList) > 0:
					jobList = c.fetchall()
				c.close()
				conn.close()
				gc.collect()
				return render_template("homepage.html", jobList=jobList)
		return render_template("newJob.html", form=form)
	except Exception as e:
		flash(e)
		return (str(e))

@app.route('/jobs/<jobid>')
def displayJob(jobid):
	c, conn = connection()
	jobData = None
	jobData = c.execute("SELECT * FROM Jobs WHERE requisitionNumber = (%s)", jobid )
	if int(jobData) > 0:
		jobData = c.fetchall()
	c.close()
	conn.close()
	gc.collect()
	return render_template("jobDetails.html", jobData=jobData)

# Below functions to diplay contents to applicants
@app.route('/jobly/list-of-jobs/')
def listOfJobs():
	c, conn = connection()
	list_of_jobs = None
	list_of_jobs = c.execute("SELECT * FROM Jobs")
	if int(list_of_jobs) > 0:
		list_of_jobs = c.fetchall()
	print "list_of_jobs: ", list_of_jobs
	c.close()
	conn.close()
	gc.collect()
	return render_template("listOfJobs.html", list_of_jobs=list_of_jobs)

@app.route('/jobs/<jobid>/apply/', methods=['GET','POST'])
def applyForJob(jobid):

	try:
		form = ApplicantForm(request.form)
		c, conn = connection()
		jobData = None
		if request.method == "POST" and form.validate():
			applicantName = form.applicantName.data
			applicantEmail = form.applicantEmail.data
			appliedDate = form.appliedDate.data
			file = request.files['file']
			if file:
				filename = secure_filename(file.filename)
				file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
				linktofile = os.path.join(app.config['UPLOAD_FOLDER'],filename)
				print "jobid: ", jobid
				print "path: ", linktofile
				c.execute("INSERT INTO Applicants (appName, appEmail, appliedDate, linkToResume, jobId) VALUES (%s, %s, %s, %s, %s)",
				(applicantName, applicantEmail, appliedDate, linktofile, jobid))
				conn.commit()
				c.close()
				conn.close()
				gc.collect()
				return redirect(url_for('thankyou'))
		jobData = c.execute("SELECT * FROM Jobs WHERE requisitionNumber = (%s)", jobid )
		if int(jobData) > 0:
			jobData = c.fetchall()
		c.close()
		conn.close()
		gc.collect()
		return render_template("jobApplication.html", jobData=jobData, form=form, jobid=jobid)
	except Exception as e:
		flash(e)
		return (str(e))



@app.route('/thankyou/')
def thankyou():
	return render_template("thankyou.html")

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

app.secret_key = "\x18\x98\\\xfdj#\x83JYh7\x84"

app.permanent_session_lifetime = timedelta(days=1)

if __name__ == "__main__":
	app.debug = True
	app.run()
