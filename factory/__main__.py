from __future__ import annotations

import json
import sys

sys.dont_write_bytecode = True

from product.core.constants import python_support  # noqa: E402



def _refuse_known_incompatible_python() -> None:
    """Refuse only an interpreter measured to break, and say nothing about the rest.

    An unverified interpreter is not refused: it is disclosed through `status`. Refusing
    versions merely because they are unfamiliar would assert something never measured,
    which is the failure this product exists to avoid.
    """
    support, detail = python_support()
    if support != "incompatible":
        return
    print(
        json.dumps(
            {
                "ok": False,
                "error": {
                    "code": "incompatible_python",
                    "message": detail,
                    "detail": {
                        "running": "%d.%d.%d" % sys.version_info[:3],
                        "executable": sys.executable,
                    },
                },
            }
        )
    )
    raise SystemExit(1)


_refuse_known_incompatible_python()

from .cli import main  # noqa: E402

raise SystemExit(main())
