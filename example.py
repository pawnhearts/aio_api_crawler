import asyncio
import random
from aiohttp import ClientSession

from api_crawler.endpoint import JsonEndpoint


def get_user_agent():
    return random.choice(["Lynx", "Mozilla"])


class Categories(JsonEndpoint):
    url = "http://127.0.0.1:8888/categories"
    params = {"page": range(100), "language": "en"}
    headers = {"User-Agent": get_user_agent}
    results_key = "*.slug"


categories = Categories()


class Posts(JsonEndpoint):
    url = "http://127.0.0.1:8888/categories/{category}/posts"
    params = {"page": range(100), "language": "en"}
    url_params = {"category": categories.iter_results()}
    results_key = "posts"

    async def comments(self, post):
        comments = Comments(
            self.session,
            url_params={"category": post.url.params["category"], "id": post["id"]},
        )
        return await comments.results()


posts = Posts()


class Comments(JsonEndpoint):
    url = "http://127.0.0.1:8888/categories/{category}/posts/{id}/comments"
    results_key = "comments.*.text"


async def worker():
    # async with ClientSession() as session:
    #     categories = Categories(session)
    #     posts = Posts(session, url_params={"category": categories.iter_results()})
    async for post in posts.iter_results():
        print(post)
        # print(post.data)
        print(await posts.comments(post))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(worker())
