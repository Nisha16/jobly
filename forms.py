from wtforms import Form, BooleanField, IntegerField, TextField, validators, PasswordField, DateField, TextAreaField
from wtforms.fields.html5 import DateField

class RegistrationForm(Form):
	firstname = TextField('Firstname', [validators.Length(min=2, max=20)])
	lastname = TextField('Lastname', [validators.Length(min=2, max=20)])
	email = TextField('Email Address', [validators.Length(min=6, max=50)])
	password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
	confirm = PasswordField('Repeat Password')

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


class mailForm(Form):
	applicantName = TextField('Applicant Name', [validators.Length(min=2, max=20)])
	subject = TextField('Applicant Email Address', [validators.Length(min=6, max=50)])
	messageBody = TextAreaField(['Message'])
	appEmail = TextField('Applicant Email Address', [validators.Length(min=6, max=50)])
