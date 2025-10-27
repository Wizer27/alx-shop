import json
from fastapi import HTTPException,FastAPI
from pydantic import BaseModel,Field
import time
import uuid
import requests
import hmac
import uvicorn
import hashlib



 


def get_key() -> str:
    with open("sec.json","r") as file:
        sec = json.load(file)
    return sec["key"]    


def verify_signature(data: dict, received_signature: str) -> bool:
    if time.time() - data.get('timestamp', 0) > 300:
        return False
    
    
    data_to_verify = data.copy()
    data_to_verify.pop("signature", None)
    
    data_str = json.dumps(data_to_verify, sort_keys=True, separators=(',', ':'))
    expected_signature = hmac.new(get_key().encode(), data_str.encode(), hashlib.sha256).hexdigest()
    
    return hmac.compare_digest(received_signature, expected_signature)

def default_basket(username:str):
    try:
        with open("basket.json","r") as file:
            data = json.load(file)
        data.append({
            "username":username,
            "basket":[]
        })
        with open("basket.json","w") as file:
            json.dump(data,file)

    except Exception as e:
        print(f"Error : {e}")


app = FastAPI()

@app.get("/")
async def main():
    return "API"

class Register(BaseModel):
    username:str
    pasw:str
    role:str
    timestamp:float  = Field(default_factory=time.time)
    siganture:str

@app.post("/register")
async def register(request:Register):
    try:
        if not verify_signature(request.signature):
            raise HTTPException(status_code = 403,detail = "Invalid signature")
        try:
            with open("users.json","r") as file:
                data = json.load(file)
            if data.get(request.username):
                raise HTTPException(status_code=400,detail = "This username is already taken")    
            data.append(
                {
                    "username":request.username,
                    "role":request.role,
                    "balance":0
                }
             )   
            with open("users.json","w") as file:
                json.dump(data,file)
            default_basket(request.username)    
        except Exception as e:
            raise HTTPException(status_code = 400,deatil = f"Error : {e}")
            
    except Exception as e:
      raise HTTPException(status_code = 400,detail = f"Error : {e}")


class Get_User_Role(BaseModel):
    username:str
@app.post("/get/user/role")
async def get_user_role(request:Get_User_Role):
    try:
        with open("users.json") as file:
            data = json.load(file)
        found  = False    
        for user in data:
            if user["username"] == request.username:
                found = True
                return user["role"]
        if not found:
            raise HTTPException(status_code = 404,detail = "Error user not found")
    except Exception as e:
        raise HTTPException(status_code = 400,detail = f"Error : {e}")


class Create_Shop(BaseModel):
    username:str
    title:str
    profile_photo:str
    signature:str
    description:str
    timestamp:float = Field(default_factory = time.time)

@app.post("/create_shop")
async def cerate_shop(request:Create_Shop):
    try:
        id = uuid.uuid4()
        with open("shops.json","r") as file:
            data = json.load(file)
        data.append({
            "username":request.username,
            "title":request.titile,
            "profile_photo":request.profile_photo,
            "description":request.description,
            "id":id,
            "cards":[]
        })
        with open("shops.json","w") as file:
            json.dump(data,file)
    except Exception as e:
        raise HTTPException(status_code = 400,detail = f"Error : {e}")

class Get_My_Shops(BaseModel):
    username:str
    signature:str
    timestamp:float = Field(default_factory = time.time)
@app.post("/user/get/shops")
async def get_my_shops(request:Get_My_Shops):
    if not verify_signature(request.model_dump(),request.siganture):
        raise HTTPException(status_code = 429,detail = "Invalid signature")
    try:
        my_shops = []
        with open("shops.json","r") as file:
            data = json.load(file)
        for shop in data:
            if shop["username"] == request.username:
                my_shops.append(shop)
        if len(my_shops == 0):
            raise HTTPException(status_code = 404,detail = "No shops")
        return my_shops
    except Exception as e:
        raise HTTPException(status_code = 400,detail = f"Error : {e}")

class Create_Card(BaseModel):
    username:str
    title:str
    description:str
    photos:str
    price:int
    shop_id:str
    signature:str
    timestamp:float = Field(default_factory=time.time)
@app.post("/create_card")
async def create_card(request:Create_Card):
    if not verify_signature(request.model_dump(),request.signature):
        raise HTTPException(status_code = 429,detail = "Invalid signature")
    try:
        ind = False
        with open("shops.json","r") as file:
            data = json.load(file)
        for shop in data:
            if shop["id"] == request.shop_id and shop["username"] == request.username:
                shop["cards"].append({
                    "title":request.title,
                    "description":request.description,
                    "photos":request.photos,
                    "price":request.price,
                    "feedbacks":[],
                    "id":str(uuid.uuid4())
                })
                ind = True
                with open("shops.json","w") as file:
                    json.dump(data,file)
                break    
        if not ind:
            raise HTTPException(status_code=404,detail = "Shop not found")
    except Exception as e:
        raise HTTPException(status_code=400,detail = f"Error : {e}")    
class Delete_Card(BaseModel):
    shop_id:str
    card_id:str
@app.post("/delete_card")
async def delete_card(request:Delete_Card):
    ind = False
    try:
        with open("shops.json","r") as file:
            data = json.load(file)
        for shop in data:
            if shop["id"] == request.shop_id:
                for i in range(len(shop["cards"])):
                    if shop["cards"][i]["id"] ==  request.card_id:
                        ind = True
                        shop["cards"].pop(i)
                        with open("shops.json","w") as file:
                            json.dump(data,file)
                        break    
        if not ind:
            raise HTTPException(status_code=400,detail="Card not found")                          
    except Exception as e:
        raise HTTPException(status_code=400,detail=f"Error : {e}")
class GetShopCards(BaseModel):
    shop_id:str
    signature:str
    timestamp:float = Field(defaul_factory = time.time)
@app.post("/get_shop_cards")
async def get_shop_cars(request:GetShopCards):
    if not verify_signature(request.model_dump(),request.signature):
        raise HTTPException(status_code = 429,detail = "Invalid signature") 
    try:
        with open("shops.json","r") as file:
            data = json.load(file)
        for shop in data:
            if shop["id"] == request.shop_id:
                return shop["cards"]
        raise HTTPException(status_code=404,detail = "Not found")        
    except Exception as e:
        raise HTTPException(status_code=400,detail = f"Error : {e}")   


class WriteTheFeedBack(BaseModel):
    username:str
    shop_id:str
    card_id:str
    stars:int
    feed_back:str
    signature:str
    timestamp:float = Field(default_factory=time.time)
@app.post("/feedback")
async def feedback(request:WriteTheFeedBack):
    if not verify_signature(request.model_dump(),request.signature):
        raise HTTPException(status_code=429,detail="Invalid signature")
    try:
        ind = False
        with open("shops.json","r") as file:
            data = json.load(file)
        for shop in data:
            if shop["id"] == request.shop_id:
                for card in shop["cards"]:
                    if card["id"] == request.card_id:
                        card["feedbacks"].append({
                            "username":request.username,
                            "stars":request.stars,
                            "feedback":request.feed_back
                        })
                        with open("shops.json","w") as file:
                            json.dump(data,file)
                        ind = True
                        break
        if not ind:
            raise HTTPException(status_code = 404,detail = "Not found")                
    except Exception as e:
        raise HTTPException(status_code=400,detail=f"Error : {e}")  



if __name__ == "__main__":
    uvicorn.run(app,host = "0.0.0.0",port = 8080)