from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    data = response.data
    if isinstance(data, dict) and "detail" in data and len(data) == 1:
        response.data = {"error": data["detail"]}
    else:
        message = data.get("detail") if isinstance(data, dict) else "Invalid request."
        response.data = {
            "error": message or "Invalid request.",
            "details": data,
        }
    return response
