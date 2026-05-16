from __future__ import annotations

from fastapi.routing import APIRoute
from starlette.routing import Match

from app.profile.router import admin_router


def _first_full_match(path: str, method: str = "GET") -> APIRoute | None:
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "root_path": "",
        "headers": [],
        "query_string": b"",
    }
    for route in admin_router.routes:
        if not isinstance(route, APIRoute):
            continue
        match, _ = route.matches(scope)
        if match is Match.FULL:
            return route
    return None


def test_profile_admin_corrections_route_is_not_shadowed_by_student_detail() -> None:
    route = _first_full_match("/admin/profile/corrections")

    assert route is not None
    assert route.endpoint.__name__ == "admin_list_corrections"


def test_profile_admin_correction_decision_route_remains_reachable() -> None:
    route = _first_full_match("/admin/profile/corrections/123/decision", method="POST")

    assert route is not None
    assert route.endpoint.__name__ == "admin_decide_correction"
