from fastapi import FastAPI, Depends , Request 
from fastapi.security import OAuth2PasswordBearer
import requests
from jose import jwt
from dotenv import load_dotenv
from pymongo import MongoClient
from app.config import CLIENT_ID, CLIENT_REDIRECT_URI, CLIENT_SECRET
load_dotenv()




# Initialize MongoDB client
mongo_client = MongoClient('localhost', 27017 )  # Update with your MongoDB connection URL
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


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Replace these with your own values from the Google Developer Console
GOOGLE_CLIENT_ID = CLIENT_ID
GOOGLE_CLIENT_SECRET = CLIENT_SECRET
GOOGLE_REDIRECT_URI = CLIENT_REDIRECT_URI



@app.get("/login/google")
async def login_google():
    return {
        "message": "Login with Google",
        "url": f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline"
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
    access_token = response.json().get("access_token")
    if response.status_code != 200:
        return {"error": "Failed to fetch user information from Google"}
    
    user_info_response = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", headers={"Authorization": f"Bearer {access_token}"})
    
    if user_info_response.status_code == 200:
        user_info = user_info_response.json()
        
        # Check if the user already exists in the database based on their email
        existing_user = users_collection.find_one({'email': user_info['email']})
        
        if not existing_user:
            # Create a new user record in your database with the user's information
            create_user_in_database(user_info)
        
        return user_info  # You can return the user's information if needed
    else:
        # Handle the case when the user information request fails
        return {"error": "Failed to fetch user information from Google"}

   

@app.get("/token")
async def get_token(token: str = Depends(oauth2_scheme)):
    return jwt.decode(token, GOOGLE_CLIENT_SECRET, algorithms=["HS256"])


    
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Successfully logged out"}

@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)