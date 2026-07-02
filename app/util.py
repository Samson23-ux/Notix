from app.api.models.user import User


def get_user_email(user: User) -> str:
    if user.type == "email":
        user_email: str = user.email
    elif user.type == "github":
        user_email: str = user.github_email
    else:
        user_email: str = user.google_email

    return user_email
