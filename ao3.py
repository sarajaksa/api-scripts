import re
import requests
import datetime
from bs4 import BeautifulSoup
from credentials import COOKIES
from consts import AO3_USER_AGENT, AO3_BASE_URL

def get_comment_from_comment_id(comment_id):
    comment_url = AO3_BASE_URL + "/comments/" + str(comment_id)
    data = requests.get(comment_url, headers={"cookie": COOKIES, "user-agent": AO3_USER_AGENT })
    soup = BeautifulSoup(data.text, features="lxml")
    comment_area = soup.find("div", class_="comments-show")
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