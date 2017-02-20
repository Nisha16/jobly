import requests

key = 'key-1fab12b2e9d23961184f9c3576c205a1'
sandbox = 'sandbox5ccaa0d8ae124f92b56643f3cada06ce.mailgun.org'

def sendMail(recipient, sender, subject, msgBody):
    request_url = 'https://api.mailgun.net/v3/nishags.co/messages'
    request = requests.post(request_url, auth=('api', key), data={
        'from': sender,
        'to': recipient,
        'subject': subject,
        'text': msgBody
    })

    print 'Status: {0}'.format(request.status_code)
    print 'Body:   {0}'.format(request.text)
