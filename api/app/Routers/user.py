from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import  Request


router = APIRouter()
templates = Jinja2Templates(directory="./Frontend/HTML") #cwd is the directory of main.py


@router.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("homepage.html", {"request": request}) #just a useless homepage.XD

@router.get("/image/")
def url_post(request: Request):
    return templates.TemplateResponse("showimag.html", {"request": request,"test":request.headers}) #the HTML file can send requests with image url in the headers. using XMLHttpRequests
