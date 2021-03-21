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

@app.get("/image/rgbdata/")
async def read_items(image_url: Optional[str] = Header(None)): #fastapi will transfer the dash from - to _
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content)) #how is the image encoded?

    rgblist = [] #the variable name is gray. Is it necessary to declare the variable before use?
    rgblist = image.split();

    rgbdict = {}
    sortedarrary = [x for x in range(256)] #used for zipping 2 lists. A waste of storage space?
    signlist = ['red', 'green', 'blue'] #used for naming the list elements. Also a waste?

    for counter in range(3):
        n, bins, patches = plt.hist(np.array(rgblist[counter]).flatten(), bins=256, facecolor='green', alpha=0.75)
        ln = n.tolist()
        iln = [int(i) for i in ln] #transfer the element type from float to int
        single_color_dict = dict(zip(sortedarrary, iln))
        # rjson = json.dumps(single_color_dict)
        rgbdict[signlist[counter]] = single_color_dict

    rgbjson = json.dumps(rgbdict)  # what's the difference between json and dictionary?

    return {"image_url": image_url,"rgbjson": rgbjson} #why cant i return image_url with request.headers.image_url or image-url?
