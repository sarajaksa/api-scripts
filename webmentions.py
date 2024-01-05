import requests
import bs4
import json
import time

def send_webmentions(article_url):
    page = requests.get(article_url)
    soup = bs4.BeautifulSoup(page.text, features="lxml")
    links_to_check = [link["href"] for link in soup.find('article').find_all('a') if "http" in link["href"] and not "sarajaksa.eu" in link["href"]]
    all_links_with_webmentions = []
    for link in links_to_check:
        try:
            data = requests.get(link)
        except:
            continue
        webmention_element = bs4.BeautifulSoup(data.text, features="lxml").find("link", rel="webmention")
        pingback_element = bs4.BeautifulSoup(data.text, features="lxml").find("link", rel="pingback")
        if not webmention_element and not pingback_element:
            continue
        elif webmention_element:
            time.sleep(1)
            webmention_link = webmention_element["href"]
            payload = 'source=' + article_url + '&target=' + link
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            try:
                response_webmentions = requests.post(webmention_link, headers=headers, data=payload)
            except:
                continue
            all_links_with_webmentions.append({
                "link": webmention_link,
                "type": "webmention",
                "code": response_webmentions.status_code,
                })
        elif pingback_element:
            pingback_link = pingback_element["href"]
            payload = f"""<?xml version="1.0" encoding="iso-8859-1"?>
                            <methodCall>
                                <methodName>pingback.ping</methodName>
                                <params>
                                    <param>
                                        <value>
                                            <string>{article_url}</string>
                                        </value>
                                    </param>
                                    <param>
                                        <value>
                                            <string>{link}</string>
                                        </value>
                                    </param>
                                </params>
                            </methodCall>"""
            time.sleep(1)
            try:
                response_pingback = requests.post(pingback_link, data=payload)
            except:
                continue
            all_links_with_webmentions.append({
                "link": pingback_link,
                "type": "pingback",
                "code": response_pingback.status_code,
                })
    return json.dumps(all_links_with_webmentions)

def list_webmentions(article_url):
    page = requests.get(article_url)
    soup = bs4.BeautifulSoup(page.text, features="lxml")
    links_to_check = [link["href"] for link in soup.find('article').find_all('a') if "http" in link["href"] and not "sarajaksa.eu" in link["href"]]
    all_links_with_webmentions = []
    for link in links_to_check:
        data = requests.get(link)
        webmention_element = bs4.BeautifulSoup(data.text, features="lxml").find("link", rel="webmention")
        pingback_element = bs4.BeautifulSoup(data.text, features="lxml").find("link", rel="pingback")
        if not webmention_element and not pingback_element:
            continue
        elif webmention_element:
            all_links_with_webmentions.append(link + " (webmention)")
        elif pingback_element:
            all_links_with_webmentions.append(link + " (pingback)")
    return "\n".join(all_links_with_webmentions)
