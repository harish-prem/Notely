from nicegui import app, ui
from fastapi import Request
import httpx;
import json

import base64
import os

LOGIN_ENDPOINT = os.getenv("LOGIN_ENDPOINT")
NO_AUTH = LOGIN_ENDPOINT == None
print("Authentication was not set up. Please check the README.md to learn how.")

if not NO_AUTH:
    TOKEN_ENDPOINT = os.getenv("TOKEN_ENDPOINT")
    REVOKE_ENDPOINT = os.getenv("REVOKE_ENDPOINT")
    USERINFO_ENDPOINT = os.getenv("USERINFO_ENDPOINT")

    CLIENT_ID=os.getenv("CLIENT_ID")
    CLIENT_SECRET=os.getenv("CLIENT_SECRET")
    HOST_ENDPOINT = os.getenv("HOST_ENDPOINT")

    REDIRECT_PATH = "/oauth2/authorize_response"
    REDIRECT_URI = HOST_ENDPOINT + "/oauth2/authorize_response"


if not NO_AUTH:
    @ui.page(REDIRECT_PATH)
    async def authentication_endpoint(request: Request):
        error = request.query_params.get("error")
        code = request.query_params.get("code")

        with ui.column().classes("w-full min-h-screen items-center justify-center gap-3"):
            if not error and not code:
                error = "bad_response"
            if not error:
                error = await trade_for_token(code, 'authorization_code')
        
            if error:
                ui.label(f"Authentication failed: {error.replace('_', ' ').title()}")
                ui.button("Try again?", on_click=login)
                return
            ui.navigate.to('/')

    async def trade_for_token(auth:str, auth_type:str):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TOKEN_ENDPOINT, 
                data = f"grant_type={auth_type}&code={auth}&redirect_uri={REDIRECT_URI}&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&scope=aws.cognito.signin.user.admin", 
                headers={'Content-Type': 'application/x-www-form-urlencoded'})
            if response.status_code == 200:
                responsejson = response.json()
                app.storage.user['access_token'] = responsejson['access_token']
                app.storage.user['id_token'] = responsejson['id_token']
                app.storage.browser['refresh_token'] = responsejson['refresh_token']
                # info = await retrieve_user_info(responsejson['access_token'])
                return
            raise Exception("Couldnt' trade token")
    async def retrieve_user_info(token) -> dict|None:
        async with httpx.AsyncClient() as client:
            response = await client.get(USERINFO_ENDPOINT, headers={'Authorization': f'Bearer {token}'})
            if response.status_code == 200:
                return dict(response.json())
        raise Exception(response, response.json())

    
def login():
    if NO_AUTH:
        return
    if LOGIN_ENDPOINT:
        ui.navigate.to(LOGIN_ENDPOINT + f"?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}")
    return


async def logout():
    if NO_AUTH:
        return
    
    refresh_token = app.storage.browser.get('refresh_token')
    if refresh_token and REVOKE_ENDPOINT:
        async with httpx.AsyncClient() as client:
            credentials = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
            await client.post(
                REVOKE_ENDPOINT,
                data=f"token={refresh_token}&client_id={CLIENT_ID}",
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': f'Basic {credentials}',
                }
            )
    app.storage.user.pop('access_token', None)
    app.storage.user.pop('id_token', None)
    login()
    return

async def logged_in_as() -> str|None:
    if NO_AUTH:
        return "user"
    if "access_token" not in app.storage.user:
        if "refresh_token" in app.storage.browser:
            #TODO: get new tokens via TOKEN_ENDPOINT
            try:
                await trade_for_token(app.storage.browser["refresh_token"], "refresh_token")
            except:
                return None
        else:
            return None
    return (await retrieve_user_info(app.storage.user["access_token"]))['sub']