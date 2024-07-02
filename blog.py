import requests
from credentials import  TOKEN_FOR_AO3_MICROPUB, GITHUB_TOKEN 
import base64

def post_short_post_to_blog(date, filename, markdown, queries):
    #if not "token" in queries or not len(queries["token"]) or queries["token"][0] != TOKEN_FOR_AO3_MICROPUB:
    #    return ""
    
    github_api_url = f"https://api.github.com/repos/sarajaksa/blog/contents/posts/{date[:4]}/{date[5:7]}/{filename}"
    post_data = {
        "message": f"Adding the post with filename {filename}",
        "committer": {
            "name": "Sara Jakša",
            "email": "sarajaksa@sarajaksa.eu"
        },
        "content": base64.encodebytes(str.encode(markdown)).decode("utf-8")
    }
    github_headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + GITHUB_TOKEN,
            "X-GitHub-Api-Version": "2022-11-28",
    }

    #response = requests.put(github_api_url, json=post_data, headers=github_headers)
    #if not response.ok:
    #    return response.text

    return "The commit was added. Please check."
    

