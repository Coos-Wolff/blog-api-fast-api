from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.exceptions import NotFoundError, ForbiddenError, EmailAlreadyExistsError, InvalidCredentialsError, PostTitleAlreadyExistsError, UnauthorizedError

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"error": str(exc)})

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: Request, exc: ForbiddenError):
        return JSONResponse(status_code=403, content={"error": str(exc)})

    @app.exception_handler(EmailAlreadyExistsError)
    async def email_already_exists_handler(request: Request, exc: EmailAlreadyExistsError):
        return JSONResponse(status_code=409, content={"error": str(exc)})

    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError):
        return JSONResponse(status_code=401, content={"error": str(exc)})

    @app.exception_handler(PostTitleAlreadyExistsError)
    async def post_title_already_exists_handler(request: Request, exc: PostTitleAlreadyExistsError):
        return JSONResponse(status_code=409, content={"error": str(exc)})

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(request: Request, exc: UnauthorizedError):
        return JSONResponse(status_code=401, content={"error": str(exc)})

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(status_code=400, content={"error": str(exc)})