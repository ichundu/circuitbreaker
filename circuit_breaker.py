#!/usr/bin/env python3

import requests
from datetime import datetime
from time import sleep

class CircuitOpenError(Exception):
    pass

class RequestFailedError(Exception):
    pass

class NotAttemptingRequestError(Exception):
    pass

class CircuitBreaker:
    def __init__(self, http_client, error_threshold, time_window):
        self.http_client = http_client
        self.error_threshold = error_threshold
        self.time_window = time_window

        # Set default state to closed
        self.state = "CLOSED"

        # Keep track of the number of errors
        self.error_count = 0

        # Save the timestamp of the last request
        self.last_request_time = None

        # When circuit is open keep track of the time left until next retry.
        self.retry_ramain_sec = 0
    
    def set_state(self, new_state):
        self.state = new_state
        print(f"Circuit Breaker state changed to {new_state}")
        return self.state

    def when_closed_circuit(self, url):
        '''
        If the circuit is closed continue sending requests normally without interruption.
        If the request fails increment the error count by 1. If the error count reaches
        our threshold raise 'CircuitOpenError' exception, otherwise just raise RequestFailedError
        exception.
        After each request (successful or not) update the last_request_time attribute.
        '''
        try:
            result = self.http_client(url)
            self.last_request_time = datetime.utcnow().timestamp()
            return result
        except:
            # The request failed, increment error count
            self.error_count += 1
            self.last_request_time = datetime.utcnow().timestamp()

            # Open the circuit if error count reaches the threshold
            if self.error_count >= self.error_threshold:
                self.set_state("OPEN")
                raise CircuitOpenError
            
            raise RequestFailedError

    def when_opened_circuit(self, url):
        '''
        If the circuit is open, first thing is to check whether a time equal to our time_window 
        parameter has elapsed since the last request. In case requests are attempted before this 
        time passes raise the RequestFailedError exception and do not attempt any connection.
        If the time has passed set the circuit state to HALF_OPEN and send a request.
        If it is successful close the circuit and reset the error count so requests can flow freely,
        otherwise keep the circuit open.
        '''
        current_time = datetime.utcnow().timestamp()

        # If a time equal to time_window has not elapsed since the last request, raise an exception
        if self.last_request_time + self.time_window >= current_time:
            self.retry_ramain_sec = self.last_request_time + self.time_window - current_time
            raise NotAttemptingRequestError
        
        print('Setting state to HALF_OPEN...')
        self.set_state("HALF_OPEN")

        try:
            result = self.http_client(url)
            # Close circuit after successful connection
            self.set_state("CLOSED")
            # Reset error_count
            self.error_count = 0
            self.last_request_time = datetime.utcnow().timestamp()
            return result
        except:
            self.error_count += 1
            self.last_request_time = datetime.utcnow().timestamp()
            # Open circuit if request failed
            self.set_state("OPEN")
            raise CircuitOpenError

    def do_request(self, url):
        ''' Handle http requests differently depending on the circuit state. '''
        if self.state == "CLOSED":
            return self.when_closed_circuit(url)
        if self.state == "OPEN":
            return self.when_opened_circuit(url)


def http_client(url):
    ''' This http client attempts requests to the given URL and catches the HTTP status code. '''
    try: 
        response = requests.get(url)
        if response.status_code == 200:
            print(f"Successful request. URL: {url}, Status code: {response.status_code}")
            return response
        if 500 <= response.status_code < 600:
            print(f"Failed request. URL: {url}, Status code: {response.status_code}")
            raise RequestFailedError("Server issue")
    except RequestFailedError:
        # print(f"Call to {url} failed")
        raise
    

if __name__ == "__main__":
    success_endpoint = "http://localhost:5000/ok"
    faulty_endpoint = "http://localhost:5000/notok"
    random_status_endpoint = "http://localhost:5000/random"

    breaker = CircuitBreaker(http_client, 5, 10)

    def test_scenario(endpoint):
        try:
            print("\n")
            breaker.do_request(endpoint)
            print(f"Error count is: {breaker.error_count}")
            print(f"Circuit state is: {breaker.state}")
            sleep(0.5)
        except RequestFailedError:
            print(f"Error count is: {breaker.error_count}")
            print(f"Circuit state is: {breaker.state}")
            sleep(0.5)
        except NotAttemptingRequestError:
            print(f"Request will not be attemted, circuit state is: {breaker.state}")
            print(f"Error count is: {breaker.error_count}")
            print(f"Retry request after {breaker.retry_ramain_sec} seconds")
            sleep(0.5)
        except CircuitOpenError:
            print(f"Circuit state is {breaker.state}")
            sleep(0.5)

    # Test 5 successful connections
    print('\n======================================================')
    print('Testing 5 successful connections...\n')
    print('======================================================')
    for i in range(5):
        test_scenario(success_endpoint)

    print('\n\nSleeping for 3 seconds...\n\n')
    sleep(3)

    # Simulate failure, after 5 failed requests, circuit opens
    print('\n======================================================')
    print('\nSimulating failure...\n')
    print('======================================================')
    for i in range(7):
        test_scenario(faulty_endpoint)

    # Wait for 12 seconds to make sure the circuit closes
    print('\n\nSleeping for 12 seconds...\n\n')
    sleep(12)

    print('\n======================================================')
    print('\nTesting /random endpoint...\n')
    print('======================================================')
    # Test '/random' endpoint
    for i in range(7):
        test_scenario(random_status_endpoint)
