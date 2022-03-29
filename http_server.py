import random

from flask import Flask
app = Flask(__name__)


@app.route('/ok')
def success_endpoint():
    return {
        "msg": "Successful request."
    }, 200


@app.route('/notok')
def faulty_endpoint():
    return {
        "msg": "Failed request."
    }, 500


@app.route('/random')
def fail_randomly_endpoint():
    r = random.randint(0, 1)
    if r == 0:
        return {
            "msg": "Successful request."
        }, 200

    return {
        "msg": "Randomly failed request."
    }, 500