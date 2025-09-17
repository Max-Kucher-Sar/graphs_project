from src.database.PSQLmodels import WellModel
from fastapi import APIRouter, Body, Depends, HTTPException, status
from src.models.Auth import get_current_user_id

wells_router = APIRouter(prefix="/wells", tags=["Скважины"])

class Well:
    def __init__(self, id: int = 0, name: str = '', is_press=False, is_debit=False, user_id: int = 0):
        self.id = id
        self.name = name
        self.is_press = is_press
        self.is_debit = is_debit
        self.user_id = user_id
    
    def add_new_well(self):
        return WellModel(name=self.name, user_id=self.user_id).create_well()
    
    def remove_well(self):
        return WellModel(id=self.id, user_id=self.user_id).delete_well()
    
    def get_wells(self):
        return WellModel(user_id=self.user_id).get_all_wells()

@wells_router.get("/all_wells")
async def get_all_wells(user_id: int = Depends(get_current_user_id)):
    return Well(user_id=user_id).get_wells()

@wells_router.put("/add_well/{well_name}")
async def add_new_well(well_name: str, user_id: int = Depends(get_current_user_id)):
    return Well(name=well_name, user_id=user_id).add_new_well()

@wells_router.delete("/remove_well/{well_id}")
async def remove_well(well_id: int, user_id: int = Depends(get_current_user_id)):
    return Well(id=well_id, user_id=user_id).remove_well()
