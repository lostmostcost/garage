import requests
import time
import random
from functools import wraps

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/537.36",
    # Add more user agents as needed
]

def retry_on_307(max_retries=30):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                response = func(*args, **kwargs)
                print(response.status_code)
                if response.status_code == 307:
                    print("Received 307 status code, retrying...")
                    retries += 1
                else:
                    return response
            raise Exception("Max retries exceeded")
        return wrapper
    return decorator

def im_not_a_robot(sleep_interval):
    def decorator(func):
        call_count = 0  # Counter for function calls

        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal call_count
            headers = kwargs.get('headers', {})
            call_count += 1
            delay = time.sleep(random.uniform(1,3))
            headers['User-Agent'] = random.choice(USER_AGENTS)
            kwargs['headers'] = headers
            
            if call_count % sleep_interval == 0:
                delay = random.uniform(25,30)
                time.sleep(delay)
                
            return func(*args, **kwargs)
        return wrapper
    return decorator

@retry_on_307()
@im_not_a_robot(sleep_interval=12)
def get_request(url, headers=None):
    if headers is None:
        headers = {}
    res = requests.get(url, headers=headers)
    return res

def generate_query_url(url, params):
    if not url.endswith('?'):
        url += '?'
    query_params = '&'.join([f"{key}={value}" for key, value in params.items() if value])
    return f"{url}{query_params}"