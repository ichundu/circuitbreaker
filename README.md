# Python Circuit Breaker

This is a simple example library that implements a circuit breaker in Python.

The picture below shows the Circuit Breaker logic:

![circuit breaker](images/state.png)

## Prerequisites

- Python 3.6+
- Install dependencies with pip:

    ```bash
    pip install -r requirements.yml
    ```

## How to test
- Run a simple flask http server which listens on `http://localhost:5000`:

    ```bash
    FLAS_APP=http_server.py flask run
    ```

    The http server has 3 endpoints:

    - [http://localhost:5000/ok](http://localhost:5000/ok) - returns status code 200.
    - [http://localhost:5000/notok](http://localhost:5000/notok) - returns status code 500.
    - [http://localhost:5000/random](http://localhost:5000/random) - returns random status code between 200 and 500.


- Open another terminal and execute the script:

    ```bash
    python circuit_breaker.py
    ```

## Test scenario:

The default circuit state is CLOSED, where requests flow freely. At first we send 5 requests to the success endpoint.

Then we send 7 requests to the faulty endpoint. When the error threshold is reached (5), we can verify by the messages in stdout that circuit state changes to OPEN after which point further requests are blocked. The circuit remains OPEN until some time has passed, 10 seconds in our case. After this time the circuit state is set to HALF_OPEN. A request is attemted, if it succeeds the circuit closes again and requests flow freely, otherwise the circuit remains OPEN until the next attempt after 10 seconds.

We add a sleep step which waits for 12 seconds and send requests to the random status endpoint. We can verify the circuit has closed (after 10 seconds).