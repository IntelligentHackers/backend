from fastapi import Request

async def get_user_ip(request: Request):
    """
    Get the user's IP address from the request.
    """
    if request.client:
        ip = request.client.host
    else:
        ip = request.headers.get("X-Forwarded-For", request.headers.get("X-Real-IP"))
    return ip
