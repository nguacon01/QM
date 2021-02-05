from flask import Flask

import app as queueManager

app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    queueManager.get_QM()

def email():
    # import yagmail
    # yag = yagmail.SMTP('dungdm91@gmail.com',"mjgvaophvtmvoljm")
    # yag.send('dungdm6191@gmail.com', subject = None, contents = 'Hello')
    return True


if __name__ == '__main__':
    index()
    app.run(host='0.0.0.0', port=9999, debug=True)