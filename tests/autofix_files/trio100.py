# type: ignore
# AUTOFIX

import trio

# error: 5, "trio", "move_on_after"
...


async def function_name():
    # fmt: off
    ...; ...; ...
    # fmt: on
    # error: 15, "trio", "fail_after"
    ...
    # error: 15, "trio", "fail_at"
    ...
    # error: 15, "trio", "move_on_after"
    ...
    # error: 15, "trio", "move_on_at"
    ...
    # error: 15, "trio", "CancelScope"
    ...

    with trio.move_on_after(10):
        await trio.sleep(1)

    with trio.move_on_after(10):
        await trio.sleep(1)
        print("hello")

    with trio.move_on_after(10):
        while True:
            await trio.sleep(1)
        print("hello")

    with open("filename") as _:
        ...

    # error: 9, "trio", "fail_after"
    ...

    send_channel, receive_channel = trio.open_memory_channel(0)
    async with trio.fail_after(10):
        async with send_channel:
            ...

    async with trio.fail_after(10):
        async for _ in receive_channel:
            ...

    # error: 15, "trio", "fail_after"
    for _ in receive_channel:
        ...

    # fix missed alarm when function is defined inside the with scope
    # error: 9, "trio", "move_on_after"

    async def foo():
        await trio.sleep(1)

    # error: 9, "trio", "move_on_after"
    if ...:

        async def foo():
            if ...:
                await trio.sleep(1)

    async with random_ignored_library.fail_after(10):
        ...
