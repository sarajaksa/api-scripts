import re
import requests
import datetime
from bs4 import BeautifulSoup
from credentials import COOKIES, AO3_USER_AGENT
from consts import AO3_BASE_URL
from ao3_auth import get_ao3_cookies, detect_logged_out_session



#from granary import ao3, rss

def get_comment_from_comment_id(comment_id):
    global COOKIES

    comment_url = AO3_BASE_URL + "/comments/" + str(comment_id)
    data = requests.get(comment_url, headers={"cookie": COOKIES, "user-agent": AO3_USER_AGENT })

    if not data.ok:
        return "Could not access the page"

    if detect_logged_out_session(data.text):
        new_cookies = get_ao3_cookies()
        COOKIES = new_cookies
        data = requests.get(comment_url, headers={"cookie": new_cookies, "user-agent": AO3_USER_AGENT })

    if not data.ok:
        return "Could not access the page"

    soup = BeautifulSoup(data.text, features="lxml")
    comment_area = soup.find("div", class_="comments-show")

    if not comment_area:
        return "Could not find the comment on the page"

    title_element = comment_area.find("h3").find("a")
    title = title_element.text
    story_link = AO3_BASE_URL + title_element["href"]
    comment = comment_area.find("li", class_="comment")
    parent_comment = [element for element in comment_area.find("ul", class_="actions").find_all("li") if "Parent Thread" in element.text]
    blog_title = "Comment AO3: " + title
    reply_element = ""
    if len(parent_comment):
        blog_title = "Reply to " + blog_title
        reply_element = "<a class=\"u-in-reply-to\" href=\"" + AO3_BASE_URL + parent_comment[0].find("a")["href"] + "\">Reply To</a>"
    slug = re.sub("[\s]", "-", re.sub("[^\s\w]+", "", blog_title.lower()))
    comment_text = "\n\n".join([paragraph.text for paragraph in comment.find("blockquote", class_="userstuff").find_all("p")])
    date_string = re.sub("[\s]+", " ", comment.find("span", class_="posted").text).strip()
    date = datetime.datetime.strptime(date_string.split(":")[0], "%a %d %b %Y %I").strftime("%Y-%m-%d")

    return f""".. title: {blog_title}
.. slug: {slug}
.. date: {date}
.. category: comment
.. type: comment

<a class=\"u-in-reply-to\" href=\"{story_link}\">Story Link</a> {reply_element} <a class=\"u-syndication\" href=\"{comment_url}\">Comment Link</a>

{comment_text}"""

def get_rss_feed(ao3_url):
    ao3_url = "https://" + ao3_url
    return rss.from_activities(ao3.ArchiveOfOurOwn().url_to_activities(ao3_url), feed_url=ao3_url.replace("https://archiveofourown.org/", "http://api.sarajaksa.eu/ao3/rss/"))

