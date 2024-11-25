# Order-Matching-System---Stock-Exchange

*How To Run This Project Locally*

* docker build -t order-matching-system-demo .
* docker run -p 80:80 -it order-matching-system-demo

*Unit Testing*

You will need to setup a venv for unit testing purposes:
* python3 -m venv venv 
* source venv/bin/activate
* pip3 install -r requirements.txt
* python -m unittest discover test