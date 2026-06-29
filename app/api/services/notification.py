from app.api.repo.notification import NotificationRepository


class NotificationService:
    def __init__(self, notis_repo: NotificationRepository):
        self._notis_repo = notis_repo
