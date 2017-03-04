from flask import Flask,render_template, request, url_for, redirect, flash, session, send_from_directory
import gc
import os


from passlib.hash import sha256_crypt
from functools import wraps
from datetime import timedelta
from werkzeug import secure_filename

from MySQLdb import escape_string as thwart

from dbConnect import connection
from forms import RegistrationForm, ApplicantForm, mailForm, JobForm
from mail import sendMail

app = Flask(__name__)


# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'resumes/'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'doc', 'docx'])

# This is the path to the upload profile photo
app.config['PROFILE_FOLDER'] = 'profile/'
# These are the extension that we are accepting to be uploaded
app.config['PHOTO_EXT'] = set(['png', 'jpg', 'jpeg', 'gif'])

# email server
MAIL_SERVER = 'localhost'
MAIL_PORT = 25
MAIL_USERNAME = None
MAIL_PASSWORD = None


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
				email = session['email']
				profile_pic = getProfilephoto(email)
				# To display created jobs  for recruiter
				jobList = None
				jobList = c.execute("SELECT * FROM Jobs WHERE creator = (%s)", session['email'])
				if int(jobList) > 0:
					jobList = c.fetchall()
					return render_template("homepage.html", data=data, jobList=jobList, profile_pic=profile_pic)
				else:
					return render_template("homepage.html", data=data, profile_pic=profile_pic)
			else:
				error = "Invalid credentials, Please try again."

		gc.collect()
		return render_template("main.html", error=error)

	except Exception as e:
		error = "Record does not exists."
		flash(e)
		return render_template('main.html', error=error)

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

@app.route('/joblist/')
@login_required
def showJobs():
	recruiter = session['email']
	c, conn = connection()
	jobList = None
	profile_pic = getProfilephoto(recruiter)
	jobList = c.execute("SELECT * FROM Jobs WHERE creator = (%s)", recruiter)
	if int(jobList) > 0:
		jobList = c.fetchall()
	c.close()
	conn.close()
	gc.collect()
	return render_template("homepage.html", jobList=jobList, profile_pic=profile_pic)

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

def getProfilephoto(email):
	c, conn = connection()
	print "email: ", email
	photo = None
	photo = c.execute("SELECT profilePhoto FROM User WHERE email = (%s)", email)
	if int(photo) > 0:
		photo = c.fetchall()
	print "photo: ", photo
	c.close()
	conn.close()
	gc.collect()
	return photo

@app.route('/<path:path>/profile/<image>')
@app.route('/profile/<image>', defaults={'path': ''})
def upload_image(image, path):
	print "fethcing image"
	return send_from_directory(app.config['PROFILE_FOLDER'],image)


@app.route('/update-profile/', methods=["GET","POST"])
@login_required
def updateProfile():
	c, conn = connection()
	user = session['email']
	profile_pic = getProfilephoto(user)
	if request.method == "POST":
		firstname = request.form.get('firstname')
		lastname = request.form.get('lastname')
		profilePhoto = request.files['photo']
		phone = request.form.get('phone')
		linkedin = request.form.get('linkedin')
		linkToPhoto = None
		if profilePhoto and allowed_photo(profilePhoto.filename):
			filename = secure_filename(profilePhoto.filename)
			profilePhoto.save(os.path.join(app.config['PROFILE_FOLDER'],filename))
			linkToPhoto = os.path.join(app.config['PROFILE_FOLDER'],filename)
			print "linkToPhoto:", linkToPhoto
		c.execute("UPDATE User SET firstname = (%s), lastname = (%s), profilePhoto = (%s), phone = (%s), linkedin = (%s) WHERE email = (%s)",(firstname, lastname, linkToPhoto, phone,linkedin, user))
		conn.commit()
		c.close()
		conn.close()
		gc.collect()
		return render_template("profile_update.html", profile_pic=profile_pic)
	userData = None
	userData = c.execute("SELECT firstName, lastName, profilePhoto, phone, linkedin FROM User WHERE email = (%s)", user )
	if int(userData) > 0:
		userData = c.fetchall()
	c.close()
	conn.close()
	gc.collect()
	return render_template("profile_update.html", userData=userData, profile_pic=profile_pic)

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
			if file and allowed_file(file.filename):
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

@app.route('/applicantslist/')
@login_required
def showApplicants():
	recruiter = session['email']
	c, conn = connection()
	applicantList = None
	profile_pic = getProfilephoto(recruiter)
	applicantList = c.execute("SELECT Jobs.title, jobs.reqDate, jobs.requisitionNumber, COUNT(Applicants.jobId) FROM Jobs LEFT JOIN Applicants ON Jobs.requisitionNumber=Applicants.jobId WHERE Jobs.creator = (%s) GROUP BY jobs.requisitionNumber, Jobs.title, jobs.reqDate ", recruiter)
	if int(applicantList) > 0:
		applicantList = c.fetchall()
	c.close()
	conn.close()
	gc.collect()
	return render_template("applicantList.html", applicantList=applicantList, profile_pic=profile_pic)

@app.route('/applicants/<jobid>/', methods=['GET', 'POST'])
@login_required
def showApplicantsForJob(jobid):
	recruiter = session['email']
	c, conn = connection()
	appData = None
	profile_pic = getProfilephoto(recruiter)
	appData = c.execute("SELECT jobId, appName, appEmail, appliedDate, linkToResume, stage FROM Applicants WHERE jobId = (%s)", jobid )
	print appData
	if int(appData) > 0:
		appData = c.fetchall()
	c.close()
	conn.close()
	gc.collect()
	return render_template("applicantsForjob.html", appData=appData, profile_pic=profile_pic)

@app.route('/applicants/<jobid>/details/<applicantname>/', methods=['GET', 'POST'])
@login_required
def showApplicantDetails(jobid, applicantname):
	recruiter = session['email']
	c, conn = connection()
	appData = None
	profile_pic = getProfilephoto(recruiter)
	appData = c.execute("SELECT appName, appEmail, jobId, linkToResume, stage FROM Applicants WHERE appName = (%s)", applicantname )
	if int(appData) > 0:
		appData = c.fetchall()
	c.close()
	conn.close()
	gc.collect()
	return render_template("applicantDetails.html", appData=appData, profile_pic=profile_pic)

@app.route('/applicants/<jobid>/details/<applicantname>/update/', methods=['GET', 'POST'])
@login_required
def updateAppDetails(applicantname, jobid):
	recruiter = session['email']
	c, conn = connection()
	profile_pic = getProfilephoto(recruiter)
	if request.method == "POST":
		stage = request.form.get('stages')
		c.execute("UPDATE Applicants SET stage = (%s) WHERE appName = (%s) and jobId = (%s)", (stage, applicantname, jobid))
		print "POST call to update"
		conn.commit()
		c.close()
		conn.close()
		gc.collect()
		return redirect(url_for('showApplicantsForJob', jobid=jobid, profile_pic=profile_pic))

@app.route('/sendMail/', methods=['GET', 'POST'])
@login_required
def mailData():
	try:
		form = mailForm(request.form)
		if request.method == 'POST' and form.validate():
			applicantName = form.applicantName.data
			subject = form.subject.data
			messageBody = form.messageBody.data
			fromEmail = session['email']
			appEmail = form.appEmail.data
			sendMail(appEmail, fromEmail, subject, messageBody)
			return redirect(url_for('thankyou'))
		return render_template("email.html", form=form)
	except Exception as e:
		flash(e)
		return (str(e))

@app.route('/contactUs/', methods=['GET', 'POST'])
def contactUs():
	try:
		if request.method == 'POST':
			name = request.form.get('name')
			email_address = request.form.get('email')
			phone = request.form.get('phone')
			message = request.form.get('message')
			message_body = "Email: " + email_address + "\n" + "phone: " + phone + "\n" + message
			email_To = 'vidya.gowdru@gmail.com'
			subject = "Website contact from " + name
			fromEmail = 'postmaster@nishags.co'
			sendMail(email_To, fromEmail, subject, message_body)
			return redirect(url_for('mainpage'))
		return render_template("main.html")
	except Exception as e:
		return (str(e))

@app.route('/')
def mainpage():
	return render_template('main.html')


@app.route('/support/')
def support():
	return render_template("support.html")

@app.route('/peers/')
@login_required
def showRecruiters():
	recruiter = session['email']
	c, conn = connection()
	recData = None
	profile_pic = getProfilephoto(recruiter)
	recData = c.execute("SELECT firstName, lastName, email FROM User")
	if int(recData) > 0:
		recData = c.fetchall()
	c.close()
	conn.close()
	gc.collect()
	return render_template("recruiters.html", recData=recData, profile_pic=profile_pic)

def allowed_photo(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['PHOTO_EXT']

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

app.secret_key = "\x18\x98\\\xfdj#\x83JYh7\x84"

app.permanent_session_lifetime = timedelta(minutes=1440)

if __name__ == "__main__":
	app.debug = True
	app.run(port=8080)
