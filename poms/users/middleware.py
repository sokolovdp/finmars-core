def is_api_request(request):
    if not request.path.startswith("/api/v1/"):
        return False

    excluded_paths = [
        "/api/v1/users/logout/",
        "/api/v1/users/login/",
        "/api/v1/users/ping/",
        "/api/v1/users/user-register/",
    ]

    return not any(request.path.startswith(path) for path in excluded_paths)
