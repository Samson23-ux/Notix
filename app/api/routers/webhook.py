from uuid import UUID
from fastapi import APIRouter, Request


from app.api.schemas.response import SuccessResponse
from app.deps import CurrentActiveUser, WebhookServiceDep
from app.api.schemas.webhook import Webhook, WebhookResponse

router = APIRouter()


@router.post(
    "/webhook",
    status_code=201,
    response_model=SuccessResponse[WebhookResponse],
    description="Register a webhook endpoint",
)
async def create_endpoint(
    request: Request,
    webhook_payload: Webhook,
    curr_user: CurrentActiveUser,
    webhook_service: WebhookServiceDep,
):
    webhook: WebhookResponse = await webhook_service.create_endpoint(curr_user, webhook_payload)
    return SuccessResponse(message="Webhook endpoint created successfully", data=webhook)


@router.delete(
    "/webhook/{endpoint_id}",
    status_code=204,
    description="Delete a webhook endpoint",
)
async def delete_endpoint(
    request: Request,
    endpoint_id: UUID,
    curr_user: CurrentActiveUser,
    webhook_service: WebhookServiceDep,
):
    await webhook_service.delete_endpoint(curr_user, endpoint_id=endpoint_id)
