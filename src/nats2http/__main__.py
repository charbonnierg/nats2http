from nats2http import settings
from nats2http.factory import start_app


if __name__ == "__main__":
    start_app(
        root_path=settings.ROOT_PATH,
        workers=settings.WEB_CONCURRENCY,
        dev=settings.DEV,
        loop=settings.AIO_LOOP,
        http=settings.HTTP_IMPL,
    )
