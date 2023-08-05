import requests
from bs4 import BeautifulSoup
import consts as BIB_CONSTS
import json
import re

OPEN_LIBRARY_COVER_SIZES = ["M", "S", "L"]

def get_cobiss_data(cobiss_url):
    book_data = {}
    book_page = requests.get("https://" + cobiss_url)
    if not book_page.ok:
        return book_data
    book_data[BIB_CONSTS.BOOK_LINK] = book_page
    if "/mkl-71/" in cobiss_url:
        book_data[BIB_CONSTS.BOOK_LOCATION] = "Mestna Knjižnica Ljubljana - Rudnik"
    if "/mkl/" in cobiss_url:
        book_data[BIB_CONSTS.BOOK_LOCATION] = "Mestna Knjižnica Ljubljana"
    book_data[BIB_CONSTS.TIMESTAMP] = "Future"
    book_soup = BeautifulSoup(book_page.text, features="html.parser")
    book_data[BIB_CONSTS.TITLE] = book_soup.find('div', class_="recordTitle").text
    book_data[BIB_CONSTS.AUTHOR] = " ".join(book_soup.find('div', class_="recordAuthor").text.split(", ")[::-1])
    book_info_elements = book_soup.find_all("div", class_="recordPrompt")
    edition_info = next(info for info in book_info_elements if "Založništvo in izdelava" in info.text)
    if edition_info:
        book_data[BIB_CONSTS.LOCATION] = edition_info.text.split('-')[1].split(":")[0].strip()
        book_data[BIB_CONSTS.PUBLISHER] = edition_info.text.split('-')[1].split(":")[1].split(',')[0].strip()
        book_data[BIB_CONSTS.YEAR] = edition_info.text.split('-')[1].split(',')[-1].strip()
    lang_info = next(info for info in book_info_elements if "Jezik" in info.text)
    if lang_info:
        book_data[BIB_CONSTS.LANGUAGE] = lang_info.text.split('-')[1].strip()
    try:
        isbn_info = next(info for info in book_info_elements if "ISBN" in info.text)
        book_data[BIB_CONSTS.ISBN] = isbn_info.text.split(' - ')[1].strip()
    except:
        pass
    return book_data

def collect_google_data(isbn):
    book_data = {}
    book_url = "https://www.googleapis.com/books/v1/volumes?q=isbn:" + correct_isbn(isbn) + "&projection=full"
    book_search_data = requests.get(book_url)
    if not book_search_data.ok:
        return book_data
    book_json = book_search_data.json()
    if book_json['totalItems'] == 0:
        return book_data
    book_data[BIB_CONSTS.ISBN] = isbn
    book_data[BIB_CONSTS.TITLE] = book_json['items'][0]['volumeInfo']['title']
    book_data[BIB_CONSTS.AUTHOR] = " and ".join(book_json['items'][0]['volumeInfo']['authors'])
    if 'publisher' in book_json['items'][0]['volumeInfo']:
        book_data[BIB_CONSTS.PUBLISHER] = book_json['items'][0]['volumeInfo']['publisher']
    book_data[BIB_CONSTS.YEAR] = int(book_json['items'][0]['volumeInfo']['publishedDate'].split('-')[0])
    book_data[BIB_CONSTS.LANGUAGE] = book_json['items'][0]['volumeInfo']['language']
    return book_data

def collect_open_library_data(isbn):
    book_data = {}
    edition_url = 'https://openlibrary.org/isbn/' + correct_isbn(isbn) + ".json"
    edition_data = requests.get(edition_url)
    if not edition_data.ok:
        return book_data
    edition_data_json = edition_data.json()
    book_data[BIB_CONSTS.ISBN] = isbn
    if 'publish_date' in edition_data_json:
        book_data[BIB_CONSTS.YEAR] = int(re.search("\d\d\d\d", edition_data_json['publish_date']).group(0))
    if 'publishers' in edition_data_json:
        book_data[BIB_CONSTS.PUBLISHER] = " and ".join(edition_data_json['publishers'])
    if 'full_title' in edition_data_json:
        book_data[BIB_CONSTS.TITLE] = edition_data_json['full_title']
    else:
        book_data[BIB_CONSTS.TITLE] = edition_data_json['title']
    work_id = edition_data_json['works'][0]['key']
    works_url = 'https://openlibrary.org' + work_id + ".json"
    work_data = requests.get(works_url)
    if not work_data.ok:
        return book_data
    work_data_json = work_data.json()
    if 'authors' in work_data_json:
        authors = [author["author"]["key"] for author in work_data_json['authors'] if author['type']['key'] == "/type/author_role"]
        authors_names = []
        for author in authors:
            author_url = 'https://openlibrary.org' + author + ".json"
            author_data = requests.get(author_url)
            if not author_data.ok:
                return book_data
            author_json = author_data.json()
            authors_names.append(author_json['name'])
        book_data[BIB_CONSTS.AUTHOR] = " and ".join(authors_names)
    return book_data

def collect_goodreads_data(isbn):
    book_data = {}
    if "https://" in isbn:
        book_url = isbn
    else:
        book_url = "https://goodreads.com/book/isbn/" + correct_isbn(isbn)

    book_page = requests.get(book_url)
    if not book_page.ok:
        return book_data
    book_soup = BeautifulSoup(book_page.text, features="html.parser")
    publication_info_element = book_soup.find("p", {"data-testid": "publicationInfo"})
    book_data_script = book_soup.find("script", {"type": "application/ld+json"})
    if publication_info_element or book_data_script:
        book_data[BIB_CONSTS.ISBN] = isbn
        publication_info_element = book_soup.find("p", {"data-testid": "publicationInfo"})
        if publication_info_element:
            book_data[BIB_CONSTS.ORIGINAL_YEAR] = int(publication_info_element.text.split(',')[1])
        book_data_script = book_soup.find("script", {"type": "application/ld+json"})
        if book_data_script:
            book_data_json = json.loads(book_data_script.contents[0])
            book_data[BIB_CONSTS.TITLE] = book_data_json['name']
            if 'inLanguage' in book_data_json:
                book_data[BIB_CONSTS.LANGUAGE] = book_data_json['inLanguage']
            book_data[BIB_CONSTS.AUTHOR] = " and ".join([author['name'] for author in book_data_json['author']])
        else:
            book_data[BIB_CONSTS.TITLE] = book_soup.find("h1").text
            book_data[BIB_CONSTS.AUTHOR] = " and ".join(
                [author.text for author in book_soup.find("div", class_="ContributorLinksList").find_all("a")])
    return book_data

def collect_bookfinder_data(isbn):
    book_data = {}
    book_url = "https://www.bookfinder.com/search/?isbn=" + correct_isbn(isbn) + "&title=&author=&lang=en&submitBtn=Search&mode=textbook&st=sr&ac=qr"
    book_page = requests.get(book_url)
    if not book_page.ok:
        return book_data
    if "Search error, please try again." in book_page.text:
        return book_data
    book_soup = BeautifulSoup(book_page.text, features="html.parser")
    book_data[BIB_CONSTS.ISBN] = isbn
    title = book_soup.find('span', id='describe-isbn-title')
    if title:
        book_data[BIB_CONSTS.TITLE] = title.text
    authors = book_soup.find('span', {"itemprop": "author"})
    if authors:
        book_data[BIB_CONSTS.AUTHOR] = " and ".join([" ".join(author.split(", ")[::-1]) for author in authors.text.split(";")])
    publisher_element = book_soup.find("span", {"itemprop": "publisher"})
    if publisher_element:
        book_data[BIB_CONSTS.PUBLISHER] = publisher_element.text.split(',')[0].strip()
        if ',' in publisher_element:
            book_data[BIB_CONSTS.YEAR] = int(publisher_element.text.split(',')[-1].strip())
    lang = book_soup.find("span", {"itemprop": "inLanguage"})
    if lang:
        book_data[BIB_CONSTS.LANGUAGE] = lang.text
    return book_data

def collect_data(isbn):
    bookfinder_data = collect_bookfinder_data(isbn)
    goodreads_data = collect_goodreads_data(isbn)
    google_data = collect_google_data(isbn)
    open_library_data = collect_open_library_data(isbn)
    data = {**bookfinder_data, **goodreads_data, **google_data, **open_library_data}
    data[BIB_CONSTS.TIMESTAMP] = "Future"
    return data

def correct_isbn(isbn):
    return isbn.replace("-", "").strip()

def change_data_to_bib(data):
    if 'isbn' in data:
        book_key = data['isbn'].lower().replace(' ', '').replace('-', '').replace(':', '').replace(';', '')
    else:
        book_key = data['title'].lower().replace(' ', '').replace('-', '').replace(':', '').replace(';', '')
    data = {bib_key: standardize_lang(bib_value) if "lang" in bib_key else bib_value for bib_key, bib_value in data.items()}
    return "@book{" \
           + book_key \
           + ",\n  " \
           + ",\n  ".join([
                bib_key + " = " + str(bib_value)
                    if type(bib_value) == int
                    else bib_key + ' = "' + str(bib_value) + '"'
                for bib_key, bib_value in data.items()]) \
           + "\n}"
    pass

def get_bib_data_from_isbn(isbn):
    data = collect_data(isbn)
    bib = change_data_to_bib(data)
    return bib

def standardize_lang(lang):
    LANG_MAP = {
        'francoski': 'fr',
        'Slovenščina': "sl",
        'Japanese': "jp",
        'srbski': "sr",
        'slovenski': "sl",
        'Serbian': "sr",
        'English': "en",
        'hrvaški': "hr",
        'srbski,': "sr",
        'German': "de",
        'angleški': "en",
        'ja': "jp",
        'Slovenian': "sl",
        'Slovak': "sk",
        'Croatian': "hr",
        'Deutsch': "de",
        'hr': "hr",
        'en': "en",
        'jp': "jp",
        'de': "de",
        "sl": "sl",
        "it": "it",
    }
    return LANG_MAP[lang]

def add_prefix_to_data(data, prefix):
    return {data_key + "_" + prefix: data_value for data_key, data_value in data.items()}

def get_full_data_from_isbn(isbn):
    bookfinder_data = add_prefix_to_data(collect_bookfinder_data(isbn), "bookfinder")
    goodreads_data = add_prefix_to_data(collect_goodreads_data(isbn), "goodreads")
    google_data = add_prefix_to_data(collect_google_data(isbn), "google")
    open_library_data = add_prefix_to_data(collect_open_library_data(isbn), "openlibrary")
    data = {**bookfinder_data, **goodreads_data, **google_data, **open_library_data}
    return data

def get_book_image_from_google(isbn):
    book_url = "https://www.googleapis.com/books/v1/volumes?q=isbn:" + correct_isbn(isbn) + "&projection=full"
    book_search_data = requests.get(book_url)
    if not book_search_data.ok:
        return None
    book_json = book_search_data.json()
    if not 'imageLinks' in book_json['items'][0]['volumeInfo']:
        return None
    for cover_link in book_json['items'][0]['volumeInfo']['imageLinks'].values():
        cover_data = requests.get(cover_link)
        if not cover_data.ok:
            continue
        return cover_data.content
    return None

def get_book_image_from_openlibrary(isbn):
    edition_url = 'https://openlibrary.org/isbn/' + correct_isbn(isbn) + ".json"
    edition_data = requests.get(edition_url)
    if not edition_data.ok:
        return None
    edition_data_json = edition_data.json()
    if 'covers' in edition_data_json:
        covers_ids = edition_data_json['covers']
        for covers_id in covers_ids:
            for size in OPEN_LIBRARY_COVER_SIZES:
                cover_url = "https://covers.openlibrary.org/b/id/" + str(covers_id) + "-" + size + ".jpg"
                cover_data = requests.get(cover_url)
                if cover_data.ok:
                    return cover_data.content
    return None

def get_book_image_from_goodreads(isbn):
    book_url = "https://goodreads.com/book/isbn/" + str(isbn)
    book_page = requests.get(book_url)
    if not book_page.ok:
        return None
    book_soup = BeautifulSoup(book_page.text, features="html.parser")
    cover_link = book_soup.find('img', class_="ResponsiveImage")['src']
    cover_data = requests.get(cover_link)
    if cover_data.ok:
        return cover_data.content
    return None

def get_book_image_from_bookfinder(isbn):
    book_url = "https://www.bookfinder.com/search/?isbn=" + str(isbn) + "&title=&author=&lang=en&submitBtn=Search&mode=textbook&st=sr&ac=qr"
    book_page = requests.get(book_url)
    if not book_page.ok:
        return None
    if "Search error, please try again." in book_page.text:
        return None
    book_soup = BeautifulSoup(book_page.text, features="html.parser")
    cover_element = book_soup.find('img', id='coverImage')
    if not cover_element:
        return None
    cover_link = cover_element['src']
    cover_data = requests.get(cover_link)
    if cover_data.ok:
        return cover_data.content
    return None

def get_book_image_from_isbn(isbn):
    google_image = get_book_image_from_google(isbn)
    if google_image:
        return google_image
    openlibrary = get_book_image_from_openlibrary(isbn)
    if openlibrary:
        return openlibrary
    goodreads = get_book_image_from_goodreads(isbn)
    if goodreads:
        return goodreads
    bookfinder = get_book_image_from_bookfinder(isbn)
    if bookfinder:
        return bookfinder
    return None

def get_book_image_from_cobiss_id(cobiss_id):
    cobiss_url = "https://plus.cobiss.net/cobiss/si/sl/bib/" + str(cobiss_id)
    book_page = requests.get(cobiss_url)
    book_soup = BeautifulSoup(book_page.text, features="html.parser")
    cover_image_element = book_soup.find('img', class_="cover")
    if not cover_image_element:
        return None
    cover_link = cover_image_element['src']
    cover_data = requests.get(cover_link)
    if not cover_data.ok:
        return None
    return cover_data.content

def get_book_image(isbn_or_cobiss_id):
    book_id = re.sub("[^\d]", "", isbn_or_cobiss_id)
    if len(book_id) == 10 or len(book_id) == 13:
        return get_book_image_from_isbn(book_id)
    return get_book_image_from_cobiss_id(book_id)


## Add the following sites
# https://isbndb.com/book/9780374275631
# https://www.biblos.si/isbn/9789610167341
# https://www.directtextbook.com/isbn/9781405862561
# https://app.thestorygraph.com/books/4cd25a5a-a3f2-48e0-bc83-ed314b751706/editions



