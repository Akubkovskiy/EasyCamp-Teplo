from typing import Optional
from pydantic import BaseModel, ConfigDict

class HouseBase(BaseModel):
    name: str
    description: Optional[str] = None
    capacity: int = 2
    
    # Dynamic Content
    wifi_info: Optional[str] = None
    address_coords: Optional[str] = None
    checkin_instruction: Optional[str] = None
    rules_text: Optional[str] = None
    
    # Promo
    promo_description: Optional[str] = None
    promo_image_id: Optional[str] = None
    guide_image_id: Optional[str] = None

class HouseCreate(HouseBase):
    pass

class HouseUpdate(HouseBase):
    name: Optional[str] = None
    capacity: Optional[int] = None

class HouseOut(HouseBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
