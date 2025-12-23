def current_page(request):
    """
    Infers the current top-level page from the URL namespace.
    Used for navbar active-link highlighting.
    """
    page = "home"

    if request.resolver_match:
        namespace = request.resolver_match.namespace

        MAP = {
            "budget": "budget",
            "accounts": "account",
            "reports": "budget",  
        }

        page = MAP.get(namespace, "home")

    return {
        "current_page": page
    }
