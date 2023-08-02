import os
import sys
from ao3 import get_comment_from_comment_id
from book import change_data_to_bib, get_cobiss_data, get_book_image, get_bib_data_from_isbn

sys.path.insert(0, os.path.dirname(__file__))

def application(environ, start_response):
    if environ['REQUEST_URI'].startswith("/ao3/comments/"):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        message = get_comment_from_comment_id(environ['REQUEST_URI'].replace("/ao3/comments/", ""))
        return [message.encode()]
    if environ['REQUEST_URI'].startswith("/book/cobiss/"):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        message = change_data_to_bib(get_cobiss_data(environ['REQUEST_URI'].replace("/book/cobiss/", "")))
        return [message.encode()]
    if environ['REQUEST_URI'].startswith("/book/isbn/"):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        message = change_data_to_bib(get_bib_data_from_isbn(environ['REQUEST_URI'].replace("/book/cobiss/", "")))
        return [message.encode()]
    if environ['REQUEST_URI'].startswith("/book/image/"):
        message = get_book_image(environ['REQUEST_URI'].replace("/book/image/", ""))
        if message:
            start_response('200 OK', [('Content-Type', 'image')])
            return [message.encode()]
        start_response('500 OK', [('Content-Type', 'text/plain')])
        return [message.encode()]
    else:
        start_response('200 OK', [('Content-Type', 'text/plain')])
        message = 'It works!\n'
        return [message.encode()]
