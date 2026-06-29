from uuid import uuid4
from typing import Annotated
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Response, Query


from app.limiter import limiter
from app.core.config import get_settings
from app.core.exceptions import AuthorizationError
from app.api.schemas.response import SuccessResponse
from app.api.schemas.user import (
    GoogleUserResponse,
    EmailUserResponse,
    GithubUserResponse,
)
from app.deps import (
    RequestDep,
    SecurityDep,
    AuthServiceDep,
    UserServiceDep,
    CurrentActiveUser,
    UnitOfWorkRepo,
)
from app.api.schemas.auth import (
    SignUpResponse,
    EmailLogin,
    EmailVerify,
    Token,
    ResendOtp,
    OtpResendResponse,
    LogoutResponse,
    ApiKeyResponse,
)

router = APIRouter()


@router.post(
    "/auth/signup",
    status_code=201,
    response_model=SuccessResponse[SignUpResponse],
    description=(
        "Sign up with email and password."
        "A verification code is sent to the user's email on completion"
    ),
)
@limiter.limit("3/5minute")
async def sign_up_with_email(
    request: Request,
    security: SecurityDep,
    email_login: EmailLogin,
    auth_service: AuthServiceDep,
    user_service: UserServiceDep,
):
    await auth_service.sign_up_with_email(email_login, user_service, security)
    return SuccessResponse(
        message=(
            "Sign up completed successfully."
            "Check your email for verification code and instructions"
        )
    )


@router.get(
    "/auth/google",
    status_code=302,
    response_class=RedirectResponse,
    description="Sign in with Google account",
)
@limiter.limit("3/5minute")
async def sign_in_with_google(request: Request, security: SecurityDep):
    redirect_uri = request.url_for("google_callback")
    return await security.oauth.google.authorize_redirect(request, redirect_uri)


@router.get(
    "/auth/google/callback",
    status_code=200,
    response_model=SuccessResponse[Token],
    description="Google redirect uri",
)
@limiter.limit("3/5minute")
async def google_callback(
    request: Request,
    response: Response,
    security: SecurityDep,
    auth_service: AuthServiceDep,
    user_service: UserServiceDep,
):
    payload: dict = await security.oauth.google.authorize_access_token(request)
    access_token, refresh_token = await auth_service.sign_up_with_google(
        payload, user_service, security
    )

    expire_time: int = get_settings().REFRESH_TOKEN_EXPIRE_TIME * 24 * 3600

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=expire_time,
        secure=get_settings().ENVIRONMENT == "production",
        samesite="lax",
    )

    return SuccessResponse(data=Token(access_token=access_token))


@router.get(
    "/auth/github",
    status_code=302,
    response_class=RedirectResponse,
    description="Sign up with github",
)
@limiter.limit("10/minute")
async def sign_in(request: Request, security: SecurityDep):
    state: str = str(uuid4())
    code_verifier: str = await security.get_code_verifier()
    code_challenge: str = await security.hash_code_challenge(code_verifier)

    client_data: dict = {"state": state, "code_verifier": code_verifier}

    request.session["client_data"] = client_data

    url = (
        f"{get_settings().GITHUB_AUTHORIZE_URL}"
        f"?client_id={get_settings().GITHUB_CLIENT_ID}"
        f"&redirect_uri={get_settings().GITHUB_CALLBACK_URL}"
        f"&scope=read:user user:email"
        f"&state={state}"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )
    return RedirectResponse(url, 302)


@router.get(
    "/auth/github/callback",
    status_code=200,
    response_model=Token,
    description="Github callback url",
)
@limiter.limit("10/minute")
async def github_callback(
    request: Request,
    response: Response,
    security: SecurityDep,
    http_request: RequestDep,
    auth_service: AuthServiceDep,
    user_service: UserServiceDep,
    error: str = None,
    state: str = None,
    code: str = None,
    code_verifier: str = None,
):
    saved_state = None

    if error:
        raise AuthorizationError()

    client_data: dict = request.session.get("client_data")

    if client_data:
        saved_state: str = client_data.get("state")
        code_verifier: str = client_data.get("code_verifier")

    access_token, refresh_token = await auth_service.sign_up_with_github(
        code, state, http_request, saved_state, code_verifier, security, user_service
    )

    expire_time: int = get_settings().REFRESH_TOKEN_EXPIRE_TIME * 24 * 3600

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=expire_time,
        secure=get_settings().ENVIRONMENT == "production",
        samesite="lax",
    )

    return SuccessResponse(data=Token(access_token=access_token))


@router.patch(
    "/auth/verify",
    status_code=200,
    response_model=SuccessResponse[EmailUserResponse],
    description="Verify account by submitting the received otp code",
)
@limiter.limit("3/5minute")
async def verify_account(
    request: Request,
    uow: UnitOfWorkRepo,
    email_verify: EmailVerify,
    auth_service: AuthServiceDep,
):
    refresh_token: str = request.cookies.get("refresh_token")
    await auth_service.verify_account(refresh_token, uow, email_verify)
    return SuccessResponse(message="User email verified successfully")


@router.post(
    "/auth/verify/resend",
    status_code=201,
    description="Resend verification code",
    response_model=SuccessResponse[OtpResendResponse],
)
@limiter.limit("3/5minute")
async def resend_otp(
    request: Request,
    otp_resend: ResendOtp,
    auth_service: AuthServiceDep,
    user_service: UserServiceDep,
):
    await auth_service.resend_otp(otp_resend, user_service)
    return SuccessResponse(
        message="OTP sent successfully. Check your email for instructions"
    )


@router.post(
    "/auth/login",
    status_code=201,
    description="Login with email and password",
    response_model=SuccessResponse[Token],
)
@limiter.limit("3/5minute")
async def login(
    request: Request,
    response: Response,
    security: SecurityDep,
    email_login: EmailLogin,
    auth_service: AuthServiceDep,
    user_service: UserServiceDep,
):
    access_token, refresh_token = await auth_service.login(
        email_login, user_service, security
    )

    expire_time: int = get_settings().REFRESH_TOKEN_EXPIRE_TIME * 24 * 3600

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=expire_time,
        secure=get_settings().ENVIRONMENT == "production",
        samesite="lax",
    )
    return SuccessResponse(
        message="Login completed successfully", data=Token(access_token=access_token)
    )


@router.post(
    "/auth/refresh",
    status_code=201,
    response_model=SuccessResponse[Token],
    description="Create new access token for user with a valid refresh token",
)
@limiter.limit("3/5minute")
async def create_new_token(
    request: Request,
    response: Response,
    auth_service: AuthServiceDep,
):
    refresh_token: str = request.cookies.get("refresh_token")
    access_token, refresh_token = await auth_service.create_auth_tokens(refresh_token)

    expire_time: int = get_settings().REFRESH_TOKEN_EXPIRE_TIME * 24 * 3600

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=expire_time,
        secure=get_settings().ENVIRONMENT == "production",
        samesite="lax",
    )
    return SuccessResponse(
        message="Token created successfully", data=Token(access_token=access_token)
    )


@router.get(
    "/auth/me",
    status_code=200,
    description="Get current active user",
    response_model=SuccessResponse[EmailUserResponse | GoogleUserResponse],
)
@limiter.limit("3/5minute")
async def get_current_user(
    request: Request,
    curr_user: CurrentActiveUser,
    auth_service: AuthServiceDep,
):
    user: EmailUserResponse | GoogleUserResponse = await auth_service.get_current_user(
        curr_user
    )
    return SuccessResponse(message="User retrieved successfully", data=user)


@router.post(
    "/auth/logout",
    status_code=201,
    response_model=SuccessResponse[LogoutResponse],
    description="Log out account",
)
@limiter.limit("3/5minute")
async def log_out(
    request: Request,
    security: SecurityDep,
    curr_user: CurrentActiveUser,
    auth_service: AuthServiceDep,
    user_service: UserServiceDep,
):
    refresh_token: str = request.cookies.get("refresh_token")
    await auth_service.logout(curr_user, user_service, refresh_token, security)
    return SuccessResponse(message="Log out completed successfully")


@router.delete("/auth", status_code=204, description="Delete account permanently")
@limiter.limit("3/5minute")
async def delete_account(
    request: Request,
    curr_user: CurrentActiveUser,
    auth_service: AuthServiceDep,
    user_service: UserServiceDep,
):
    refresh_token: str = request.cookies.get("refresh_token")
    await auth_service.delete_account(curr_user, user_service, refresh_token)


@router.post(
    "/auth/keys",
    status_code=201,
    response_model=SuccessResponse[ApiKeyResponse],
    description="Create api key. Api keys are valid until deleted",
)
@limiter.limit("3/5minute")
async def create_api_key(
    request: Request,
    curr_user: CurrentActiveUser,
    auth_service: AuthServiceDep,
):
    api_key: ApiKeyResponse = await auth_service.create_api_key(curr_user)
    return SuccessResponse(message="Api key created successfully", data=api_key)


@router.get(
    "/auth/keys",
    status_code=200,
    response_model=SuccessResponse[ApiKeyResponse],
    description="Get all created keys",
)
@limiter.limit("3/5minute")
async def get_all_api_keys(
    request: Request,
    curr_user: CurrentActiveUser,
    auth_service: AuthServiceDep,
    sort: Annotated[str, Query(description="Sort by created_at")] = None,
    order: Annotated[str, Query(description="Order in asc or desc")] = "asc",
    cursor: Annotated[str, Query()] = None,
    limit: Annotated[int, Query()] = 10,
):
    api_key: list[ApiKeyResponse] = await auth_service.get_all_api_keys(curr_user)
    return SuccessResponse(message="Api keys retrieved successfully", data=api_key)


@router.get(
    "/auth/keys/{key}",
    status_code=200,
    response_model=SuccessResponse[ApiKeyResponse],
    description="Get created api key",
)
@limiter.limit("3/5minute")
async def get_api_key(
    key: str,
    request: Request,
    curr_user: CurrentActiveUser,
    auth_service: AuthServiceDep,
):
    api_key: ApiKeyResponse = await auth_service.get_api_key(curr_user, key)
    return SuccessResponse(message="Api key retrieved successfully", data=api_key)


@router.delete(
    "/auth/keys/{key}",
    status_code=204,
    description="Delete api key",
)
@limiter.limit("3/5minute")
async def delete_api_key(
    key: str,
    request: Request,
    security: SecurityDep,
    curr_user: CurrentActiveUser,
    auth_service: AuthServiceDep,
):
    await auth_service.delete_api_key(curr_user, key)
