import trio

# a
# b
with trio.move_on_after(10):  # error: 5, "trio", "move_on_after"
    # c
    # d
    print(1)  # e
    # f
    # g
    print(2)  # h
    # i
    # j
    print(3)  # k
    # l
    # m
# n

with trio.move_on_after(10):  # error: 5, "trio", "move_on_after"
    ...


# a
# b
# fmt: off
with trio.move_on_after(10): ...;...;... # error: 5, "trio", "move_on_after"
# fmt: on
# c
# d

# Doesn't autofix With's with multiple withitems
with (
    trio.move_on_after(10),  # error: 4, "trio", "move_on_after"
    open("") as f,
):
    ...


# multiline with, despite only being one statement
with (  # a
    # b
    # c
    trio.move_on_after(  # error: 4, "trio", "move_on_after"
        # d
        9999999999999999999999999999999999999999999999999999999  # e
        # f
    )  # g
    # h
):  # this comment is kept
    ...

# fmt: off
with (  # a
    # b
    trio.move_on_after(10)  # error: 4, "trio", "move_on_after"
    # c
): ...; ...; ...
# fmt: on
