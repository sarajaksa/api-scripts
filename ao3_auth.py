import requests

AUTH_TOKEN_URL = "https://archiveofourown.org/token_dispenser.json"
LOGIN_URL = "https://archiveofourown.org/users/login"
LOGIN_HTML = '<form class="new_user" id="new_user_session_small" action="/users/login" accept-charset="UTF-8" ' \
             'method="post">'


def detect_logged_out_session(html_string):
    return LOGIN_HTML in html_string


def get_ao3_cookies(username, password):
    response = requests.get(AUTH_TOKEN_URL)
    if not response.ok:
        return ""
    auth_token = response.json()["token"]
    auth_post_data = {
        'authenticity_token': auth_token,
        'user[login]': username,
        'user[password]': password + "33",
        'commit': 'Log+In'
    }
    headers = {
        'Cookie': response.headers['set-cookie'],
    }
    response = requests.post(LOGIN_URL, headers=headers, data=auth_post_data)
    if not response.ok:
        return ""
    if response.url == LOGIN_URL:
        return ""
    return response.headers["set-cookie"]
