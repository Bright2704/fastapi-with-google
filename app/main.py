from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from dotenv import load_dotenv
from pymongo import MongoClient
from app.config import CLIENT_ID, CLIENT_REDIRECT_URI, CLIENT_SECRET
from fastapi import Depends
from fastapi import FastAPI, Request  # Importing Request here
import requests
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


# Initialize MongoDB client
mongo_client = MongoClient('localhost', 27017)  # Update with your MongoDB connection URL
db = mongo_client['mongo-db']  # Update with your database name
users_collection = db['users']  # Collection to store user records

# Define the function to create a user record in the database
def create_user_in_database(user_info):
    user_record = {
        'email': user_info['email'],
        'name': user_info['name'],
        'picture': user_info['picture'],
    }
    users_collection.insert_one(user_record)


class Vote(BaseModel):
    name: str
    email: str
    img: str


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Replace these with your own values from the Google Developer Console
GOOGLE_CLIENT_ID = CLIENT_ID
GOOGLE_CLIENT_SECRET = CLIENT_SECRET
GOOGLE_REDIRECT_URI = CLIENT_REDIRECT_URI

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
   
@app.post("/votes/")
async def create_vote(vote: Vote):
    # Check if an entry with the same email already exists
    existing_vote = users_collection.find_one({"email": vote.email})
    
    # If an entry exists, return an appropriate response
    if existing_vote:
        return {"error": "A vote with this email already exists"}

    # If no entry exists, insert the new vote
    result = users_collection.insert_one(vote.dict())
    return {"name": vote.name, "email": vote.email, "img": vote.img}

@app.get("/login")
async def login_google(request: Request):
    return {
        "message": "Login with Google",
        "url": f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline",
        
    }




@app.get("/auth")
async def auth_google(code: str):
    token_url = "https://accounts.google.com/o/oauth2/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    response = requests.post(token_url, data=data)
    
    if response.status_code != 200:
        return {"error": "Failed to fetch access token from Google"}

    # Extracting the access token from the response
    access_token = response.json().get("access_token")

    user_info_response = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", headers={"Authorization": f"Bearer {access_token}"})
    
    if user_info_response.status_code == 200:
        user_info = user_info_response.json()
        
        existing_user = users_collection.find_one({'email': user_info['email']})
        if not existing_user:
            create_user_in_database(user_info)

        # Return both user information and access token
        return {"user_info": user_info, "access_token": access_token}
    else:
        return {"error": "Failed to fetch user information from Google"}


@app.get("/token")
async def get_token(token: str = Depends(oauth2_scheme)):
    return jwt.decode(token, GOOGLE_CLIENT_SECRET, algorithms=["HS256"])




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
