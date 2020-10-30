from aiohttp import web
from faker import Faker

routes = web.RouteTableDef()
faker = Faker()


@routes.get("/categories")
async def categories(request):
    page = int(request.query.get("page", 0))
    if page > 0:
        raise web.HTTPNotFound
    return web.json_response(
        [{"name": faker.name(), "slug": faker.domain_word()} for i in range(10)]
    )


@routes.get("/categories/{slug}/posts")
async def posts(request):
    page = int(request.query.get("page", 0))
    if page > 3:
        raise web.HTTPNotFound
    return web.json_response(
        {
            "posts": [
                {'id': faker.random_int(), "title": faker.name(), "slug": faker.domain_word()} for i in range(10)
            ],
            "page": page,
            'category': request.match_info['slug'],
        }
    )

@routes.get("/categories/{slug}/posts/{id}/comments")
async def comments(request):
    return web.json_response(
        {
            "comments": [
                {"name": faker.name(), "text": faker.text()} for i in range(3)
            ]
        }
    )

app = web.Application()
app.add_routes(routes)
web.run_app(app, host='127.0.0.1', port=8888)
