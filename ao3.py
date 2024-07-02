import re
import requests
import datetime
from bs4 import BeautifulSoup
from credentials import COOKIES, AO3_USER_AGENT, TOKEN_FOR_AO3_MICROPUB, GITHUB_TOKEN 
from consts import AO3_BASE_URL
from ao3_auth import get_ao3_cookies, detect_logged_out_session
import base64
import json


from granary import ao3, rss

def get_comment_from_comment_id(comment_id, micropub_queries):

    comment_id = comment_id.split("?")[0]

    global COOKIES

    comment_url = AO3_BASE_URL + "/comments/" + str(comment_id)
    data = requests.get(comment_url, headers={"cookie": COOKIES, "user-agent": AO3_USER_AGENT })

    if not data.ok:
        return "Could not access the page"

    if detect_logged_out_session(data.text):
        return "Requires new Cookies. Please refresh them."

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
        reply_element = ";Archive of Our Own Comment:" + AO3_BASE_URL + parent_comment[0].find("a")["href"]
    slug = re.sub("[\s]", "-", re.sub("[^\s\w]+", "", blog_title.lower())) + "-" + comment_id
    comment_text = "\n\n".join([paragraph.text for paragraph in comment.find("blockquote", class_="userstuff").find_all("p")])
    date_string = re.sub("[\s]+", " ", comment.find("span", class_="posted").text).strip()
    date = datetime.datetime.strptime(date_string.split(":")[0], "%a %d %b %Y %I").strftime("%Y-%m-%d")

    blog_comment_text =  f""".. title: {blog_title}
.. slug: {slug}
.. date: {date}
.. category: comment
.. type: comment
.. rss: False
.. syndication: Archive of Our Own (AO3):{comment_url}
.. replyto: Archive Of Our Own Story {title}:{story_link}{reply_element}

{comment_text}"""

    if not "token" in micropub_queries or not len(micropub_queries["token"]) or micropub_queries["token"][0] != TOKEN_FOR_AO3_MICROPUB:
        return blog_comment_text

    post_lang = "en"
    if "lang" in micropub_queries and len(micropub_queries["lang"]) and micropub_queries["lang"][0]:
        post_lang = micropub_queries["lang"]

    github_api_url = f"https://api.github.com/repos/sarajaksa/blog/contents/posts/{date[:4]}/{date[5:7]}/{slug}.{post_lang}.md"
    post_data = {
        "message": f"Adding the AO3 comment with ID {comment_id}",
        "committer": {
            "name": "Sara Jakša",
            "email": "sarajaksa@sarajaksa.eu"
        },
        "content": base64.encodebytes(str.encode(blog_comment_text)).decode("utf-8")
    }
    github_headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + GITHUB_TOKEN,
            "X-GitHub-Api-Version": "2022-11-28",
    }

    response = requests.put(github_api_url, json=post_data, headers=github_headers)
    if not response.ok:
        return response.text

    return "The commit was added. Please check."



def get_rss_feed(ao3_url):
    ao3_url = "https://archiveofourown.org" + ao3_url.replace("https://archiveofourown.org", "").replace("archiveofourown.org", "")
    return rss.from_activities(ao3.ArchiveOfOurOwn().url_to_activities(ao3_url), feed_url=ao3_url.replace("https://archiveofourown.org/", "http://api.sarajaksa.eu/ao3/rss/"))

