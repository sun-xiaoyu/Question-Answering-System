# Question-Answering-System (QAS): 
### Application link: [wikianswers.herokuapp.com](http://wikianswers.herokuapp.com)
A factoid based question answering system

<kbd>![Screenshot of system](https://github.com/Upa005/Question-Answering-System/blob/master/Description/screenshot_of_qas.png)</kbd>

QAS is a system that automatically answer questions posed by humans in natural language query. Natural language (e.g. English) is the common way of sharing knowledge.

## Characteristics of the factoid based QAS:
The Question Answering System (QAS):
* tries to answer factoid based questions.
* provides concise facts about the question.
  For example, "where is Taj Mahal located?", “Who is the father of nation of India?”.
* is a web-based QAS.
* answer open-domain fact based questions.
* uses wikipedia and google search pages to extract concise answers.

## Block diagram of the system:
![Block diagram of system](https://github.com/Upa005/Question-Answering-System/blob/master/Description/block_diagram_qas.png)

## Setup Instructions

* Clone the source
	```
	git clone https://github.com/Upa005/Question-Answering-System.git
	```
  
*  Requirements <br />
	Python version : 2.7  <br />
  Operating System: Windows

  
* Python Packages required <br />

  nltk <br />
  flask <br />
  gunicorn <br />
  unidecode <br />
  wolframalpha <br />
  wikipedia <br />
  gevent <br />
  flask_bootstrap <br />
  flask_appconfig <br />
  flask_wtf <br />
  wtforms <br />
  google <br />



* Generate Wolframalpha API Key (You can use our to test things)

	1. Visit the [Wolframalpha APIs Console](https://products.wolframalpha.com/api/) and log in with your Wolframalpha account.

	2. In the API admin page, you will get your API Key.
  
  3. Open Question-Answering-System/app.py program. 
     Search this sentence in the program. (At line number 28)
     ```
     app.config['SECRET_KEY']= ## insert your secret key
     ```
     Now insert your secret key after '=' sign
     ```
     Example: app.config['SECRET_KEY']= '\\ffedg0890489574'

     ```
 4. Save the file.


## To Run
1. Install python 2.7 to your system
2. Install the packages givn in the requirements.txt file
3. Open command prompt.
4. Go to the directory in command prompt.
5. Type in command prompt: 
    ```
    py -2 app.py
    ```
6. Now run the browser and type localhost:9191/
7. Input your question. (Make sure, you are connected to Internet)
8. Wait for the answer

