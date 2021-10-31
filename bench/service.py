import os
import random
import string

from nats import connect


PAYLOAD_SIZE = os.environ.get("PAYLOAD_SIZE", 128)


def random_payload(length: int = PAYLOAD_SIZE) -> bytes:
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length)).encode("utf-8")


async def main():
    nc = await connect()
    sub = await nc.subscribe("test", "test-service")
    payload = random_payload()
    async for msg in sub.messages:
        await nc.publish(msg.reply, payload, headers={"content-type": "text/plain"})


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

