from typing import Optional
from fastapi import FastAPI, Request, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
from PIL import Image
from io import BytesIO
import numpy as np
import matplotlib.pyplot as plt
import json

#uvicorn main:app --reload
app = FastAPI()
templates = Jinja2Templates(directory="./HTML")

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("homepage.html", {"request": request}) #just a useless homepage.XD

@app.get("/image/")
def url_post(request: Request):
    return templates.TemplateResponse("showimag.html", {"request": request,"test":request.headers}) #the HTML file can send requests with image url in the headers. using XMLHttpRequests

def extract_colour(image): #split the image into three: red, green, blue. Then merge the color histogram in a dictionary of lists which have int elements.
    rgbdict = {}
    for colour, colour_name in zip(image.split(), ["red", "green", "blue"]): #We need to zip the two lists, otherwise the for loop will regard the two lists as two elements of a new list.
        n,bins = np.histogram(colour, bins=256)  # the return value bins is the width list of columns(from 0 to 256-1). We still need a sorted list.
        int_list_n = [int(i) for i in n]    #n is in numpy.ndarrrary type. Zipping the two list will have elements as numpy.int64, which can not be transfered into json. Variable type conversion is required.
        rgbdict[colour_name] = dict(zip(range(256), int_list_n)) 
    return rgbdict

@app.get("/image/rgbdata/")
async def read_items(image_url: Optional[str] = Header(None)): #fastapi will transfer the dash from - to _
    response = requests.get(image_url) #send get request to the image_url
    image = Image.open(BytesIO(response.content))

    rgbdict = extract_colour(image)

    return rgbdict
