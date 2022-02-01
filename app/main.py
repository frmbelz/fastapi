from typing import Optional
import base64
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import http3
import pydantic
import os
import requests
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json

app = FastAPI()
client = http3.AsyncClient()


from pathlib import Path
from pprint import pprint
BASE_DIR = Path(__file__).resolve().parent
#print(BASE_DIR)
#direct = str(Path(BASE_DIR, 'templates'))
#templates = Jinja2Templates(directory=str(Path(BASE_DIR, 'templates')))
templates_dir = os.path.abspath(os.path.expanduser("templates"))
#templates = Jinja2Templates(directory="templates")
templates = Jinja2Templates(directory=templates_dir)
static_dir = os.path.abspath(os.path.expanduser("static"))
app.mount("/static", StaticFiles(directory=static_dir), name="static")

async def get_info(url: str):
    r = await client.get(url)
    return r.text

@app.get("/v1/info")
async def read_info():
    response = await get_info("http://127.0.0.1:8080/v1/info")
    return response

# debugging the reading of a file
#cwd = os.getcwd()
#files = os.listdir(cwd)

async def get_template(img: str):
    print("image: " + img)
    url = "http://127.0.0.1:8080/v1/create-template"
    image_path = static_dir + "/images/" + img
    print("image path: " + image_path)
    encoded = base64.b64encode(open(image_path, "rb").read())
    # remove leading b in front of a string
    data = {"ImageData": encoded.decode('utf-8')}

    response = await client.post(url, json=data )
    return response.text

@app.post("/v1/create-template")
async def create_template(request: Request):
    checked_images = await request.json()
    print(checked_images)
    response = await get_template()
    return response

async def post_compare(compare_json: {}):
    url = "http://localhost:8080/v1/compare-list"
    # sample format to send to API
    #data = {
    #        "SingleTemplate": 
    #            {
    #                "Template":"LTExMTAxMTAwMDAwMTEwMTAxMTAwMTAxMTEwMTAwMDA="
    #            },
    #        "TemplateList": [
    #            {"Template":"MTExMTAxMTExMDEwMTExMDEwMDEwMTAxMTAxMDEx"},
    #            {"Template":"LTExMTAwMTAxMDEwMTExMTAwMTAxMDExMDAwMDEx"},
    #            {"Template":"MTAwMTAxMDEwMDAxMDEwMDAwMDAwMTExMDEwMDExMQ=="}
    #        ]
    #    }

    response = await client.post(url, json=json.loads(compare_json) )
    return response.text

async def build_compare(single_templ: str, templ_list: []):
    combined_str = ''
    list_len = len(templ_list)
    i = 1
    for item in templ_list:
        combined_str += str(item)
        if i < list_len: combined_str += ", "
        i += 1

    data = '{"SingleTemplate" : '+single_templ+', "TemplateList" : ['+combined_str+']}'
    return data

@app.post("/v1/compare-list")
async def compare_list():
    
    response = await post_compare()
    return response

@app.post("/compare-images", include_in_schema=False)
async def create_template(request: Request):
    print("in compare-images")
    checked_images = await request.json()
    print(checked_images)
    single_img = checked_images['send']['single']
    template_list = []
    for img in checked_images['send']['templ_list']:
        print(img)
        templ = await get_template(img)
        print(templ)
        template_list.append(templ)
    print("all templates in an array")
    print(template_list)
    print("single: " + single_img)
    single_template = await get_template(single_img)
    json_str = await build_compare(single_template, template_list)
    scores = await post_compare(json_str)
    return scores

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request):
    data = {
        "page": "Welcome to MDTF testing"
    }
    return templates.TemplateResponse("index.html", {"request": request, "data": data})

@app.get("/page/{page_name}", response_class=HTMLResponse, include_in_schema=False)
async def page(request: Request, page_name: str):
    data = {
        "page": page_name
    }
    page_full = page_name + ".html"
    return templates.TemplateResponse(page_full, {"request": request, "data": data})





