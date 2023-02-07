# NOANYIO - don't run it with substitutions
import anyio
import trio

try:
    ...
except trio.Cancelled:  # TRIO103: 7, "trio.Cancelled"
    ...
except anyio.get_cancelled_exc_class():  # TRIO103: 7, "anyio.get_cancelled_exc_class()"
    ...
except:  # safe
    ...

try:
    ...
except anyio.get_cancelled_exc_class():  # TRIO103: 7, "anyio.get_cancelled_exc_class()"
    ...
except trio.Cancelled:  # TRIO103: 7, "trio.Cancelled"
    ...
except:  # safe
    ...

try:
    ...
except anyio.get_cancelled_exc_class():  # TRIO103: 7, "anyio.get_cancelled_exc_class()"
    ...
except:  # safe ?
    ...

try:
    ...
except trio.Cancelled:  # TRIO103: 7, "trio.Cancelled"
    ...
except:  # safe ?
    ...

# Check we get the proper suggestion when both are imported
try:
    ...
except BaseException:  # TRIO103_anyio_trio: 7, "BaseException"
    ...

try:
    ...
except:  # TRIO103_anyio_trio: 0, "bare except"
    ...
