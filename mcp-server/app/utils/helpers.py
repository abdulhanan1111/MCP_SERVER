# Helper functions for the MCP server

def format_response(data: dict, message: str = "Success") -> dict:
    return {
        "status": "success",
        "message": message,
        "data": data
    }

def format_error(message: str, details: str = None) -> dict:
    error_resp = {
        "status": "error",
        "message": message
    }
    if details:
        error_resp["details"] = details
    return error_resp
