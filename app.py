import re
import gevent.monkey
from gevent.pywsgi import WSGIServer
import logging

from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from flask_appconfig import AppConfig
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from qasystem import QAsystem

qa = QAsystem()
gevent.monkey.patch_all()


class ExampleForm(FlaskForm):
    question = StringField('', description='', validators=[DataRequired()])
    submit_button = SubmitField('Go')


class ExampleForm1(FlaskForm):
    reference_page_url = StringField('', description='', validators=[DataRequired()])
    submit_button = SubmitField('Search here')


def create_app(configfile=None):
    app = Flask(__name__)
    AppConfig(app, configfile)
    Bootstrap(app)
    question_asked = []
    app.config['SECRET_KEY']= '3V3PT7-TXHKXVKX82'

    @app.route('/', methods=('GET', 'POST'))
    def index():
        if request.method == 'POST':
            reference_page_url = None
            try:
                question = request.form['question']
            except KeyError:
                app.logger.info("No questions are given, try the 2nd route")

                try:
                    question = question_asked[-1]
                    reference_page_url = request.form['reference_page_url']
                    app.logger.info(f"User has given a reference page: {reference_page_url}")
                except:
                    print('I got another exception that I cannot explain')
                    raise

            app.logger.info(question)
            if not reference_page_url:
                question_asked.append(question)
                answer = qa.ask(question)
            else:
                answer = qa.ask(question, reference_page_url)
            app.logger.info(re.sub('\n\n', '\n', answer))
            answer = re.sub('([(].*?[)])', "", answer)

            form1 = ExampleForm1()
            return render_template('answer.html', answer=answer, question=question, form=form1)

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

