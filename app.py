import re
import gevent.monkey
from gevent.pywsgi import WSGIServer
import logging

from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from flask_appconfig import AppConfig
from flask_wtf import Form, RecaptchaField
from wtforms import TextField, HiddenField, ValidationError, RadioField, BooleanField, SubmitField
from wtforms.validators import Required
from qasystem import QAsystem

qa = QAsystem()
gevent.monkey.patch_all()
# from give_answer import answer_question
# import unicodedata
# import wolframalpha
# import wikipedia

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class ExampleForm(Form):
    question = TextField('', description='', validators=[Required()])
    submit_button = SubmitField('Go')


def create_app(configfile=None):
    app = Flask(__name__)
    AppConfig(app, configfile)
    Bootstrap(app)


    app.config['SECRET_KEY']= '3V3PT7-TXHKXVKX82'## insert your secret key


    @app.route('/', methods=('GET', 'POST'))
    def index():
        if request.method == 'POST':
            try:
                question = request.form['question']
            except KeyError:
                print('key eroor')
                print('I got a KeyError - reason')
            except:
                print('I got another exception, but I should re-raise')
                raise


            logging.info(question)
            # answer = answer_question(question)
            answer = qa.ask(question)
            logging.info(answer)
            answer=re.sub('([(].*?[)])',"",answer)

            return render_template('answer.html', answer=answer, question=question)

        form = ExampleForm()
        return render_template('index.html', form=form)



    return app

# create main callable
app = create_app()
app.logger.setLevel(logging.INFO)

if __name__ == '__main__':
    http_server = WSGIServer(('127.0.0.1', 5666), app)
    print("starting debug server on port 5666")
    http_server.serve_forever()

