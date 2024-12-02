def create_route_with_prefix(route):
    api_version = "v1"
    api_prefix = f"/api/{api_version}"
    # Ensure consistent formatting for prefixed routes
    return f"{api_prefix}{route}"
