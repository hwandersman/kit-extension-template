
from omni.services.core import routers
import carb
import omni.usd
from pxr import Usd, Sdf

from typing import Optional
from pydantic import BaseModel, Field

import carb
http_server_port = carb.settings.get_settings().get_as_int("exts/omni.services.transport.server.http/port")
carb.log_info(f"The OpenAPI specifications can be accessed at: http://localhost:{http_server_port}/docs")

class SetSelectedEntityRequestModel(BaseModel):
    """Request to set selected entity id."""

    entity_id: Optional[str] = Field(
        None,
        title="Selected entity id",
        description="The id of the selected entity.",
    )

class SetSelectedEntityResponseModel(BaseModel):
    """Response to the request to select entity."""
    
    success: bool = Field(
        ...,
        title="Success",
        description="Flag indicating if the request was successful.",
    )
    errorMessage: Optional[str] = Field(
        None,
        title="Error message",
        description="Details about the error that occurred, in case of failure.",
    )

class GetSelectedEntityResponseModel(BaseModel):
    """Response to the request to get selected entity id."""

    entity_id: Optional[str] = Field(
        None,
        title="Selected entity id",
        description="The id of the selected entity.",
    )
    
router = routers.ServiceAPIRouter()

def get_context():
  return omni.usd.get_context()

def get_attribute_value(prim: Usd.Prim, attribute_name: str):
    """
    See: https://graphics.pixar.com/usd/release/api/class_usd_attribute.html
    Args:
        prim: The prim owner of the attribute.
        attribute_name: The name of the attribute to retrieve.
    Return:
        The value of the attribute, see https://graphics.pixar.com/usd/release/api/_usd__page__datatypes.html
        for the return types.
        For example, for `float3`, the return type will be `Gf.Vec3f`.
    """
    attr = prim.GetAttribute(attribute_name)
    return attr.Get()
  
@router.get(
    "/selected_entity",
    summary="Return selected entity id.",
    description="Return selected entity id.",
    response_model=GetSelectedEntityResponseModel,
)
async def get_selected_entity() -> GetSelectedEntityResponseModel:
    usd_context = get_context()
    stage = usd_context.get_stage()
    prim_paths = usd_context.get_selection().get_selected_prim_paths()
    carb.log_info("selected prim paths " + str(prim_paths))
    
    if not prim_paths:
        return GetSelectedEntityResponseModel(entity_id=None)

    prim = stage.GetPrimAtPath(prim_paths[0])
    val = get_attribute_value(prim, "entity_id")
    carb.log_info("entity_id " + str(val))
    return GetSelectedEntityResponseModel(entity_id=str(val))

@router.post(
    "/selected_entity",
    summary="Return selected entity id.",
    description="Return selected entity id.",
    response_model=SetSelectedEntityResponseModel,
)
def set_selected_entity(request: SetSelectedEntityRequestModel) -> SetSelectedEntityResponseModel:
    entity_id = request.entity_id
    carb.log_info("set_selected_entity " + str(entity_id))
    context = get_context()
    context.get_selection().set_selected_prim_paths(['/World/Interaction/' + entity_id], True)
    return SetSelectedEntityResponseModel(success=True)
