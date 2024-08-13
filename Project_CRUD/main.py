### Import Libraries
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse,PlainTextResponse
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError



import uvicorn
from bson import ObjectId

### Bind app
app= FastAPI()
### create jinja instance and define directory where to store the html files
templates=Jinja2Templates(directory='templates')

html_path = "templates/error_display.html"

# MongoDB connection details
MONGO_DB_URL="mongodb://localhost:27017"
DATABASE_NAME="testdb"
COLLECTION_NAME='user_details'

### Mongo Connection from API
client=AsyncIOMotorClient(MONGO_DB_URL)
database=client[DATABASE_NAME]
collection=database[COLLECTION_NAME]

### Render the initial template
@app.get("/",response_class=HTMLResponse )
async def render_form(request:Request):
    return templates.TemplateResponse("registration.html",{"request":request})

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

### submit_form (with document id- editing already existing record)
@app.post("/submit_form/{document_id}")
async def submit_form(
        request: Request,
        document_id:str,
        fname: str = Form(...),
        lname: str = Form(...),
        DOB: str = Form(...),
        city: str = Form(...),
        state: str = Form(...),
        country: str = Form(...),
        update: int = Form(0),
    ):
    try:
        if document_id:
            id=ObjectId(document_id)
            obj_id=ObjectId(id)
            result=collection.update_one({'_id':obj_id},{'$set':{
                "first_name": fname,
                "last_name": lname,
                "dob": DOB,
                "city": city,
                "state": state,
                "country": country
            }})
            return templates.TemplateResponse('message_after_edit.html',{'request':request,'message':'Your details have been updated'})
    except HTTPException as e:
        return templates.TemplateResponse('error_display.html',{'status_code':e.status_code,'detail':e.detail,'request':request})
    except Exception as e:
        return templates.TemplateResponse('error_display.html',{'status_code':500,'detail':'Internal Server Error','request':request})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    # Customize the error message or redirect to an error page
    error_message = "Invalid input data. Please check your form fields."
    return templates.TemplateResponse('error_display.html', {'status_code': 422, 'detail': 'Some input is missing','request':request})

    #return PlainTextResponse(content=error_message, status_code=422)

### submit new form
@app.post("/submit_form")
async def submit(
        request:Request,
        fname: str = Form(...),
        lname: str = Form(...),
        DOB: str = Form(...),
        city: str = Form(...),
        state: str = Form(...),
        country: str = Form(...),
        update: int = Form(0),
    ):
    document = {
        "first_name": fname,
        "last_name": lname,
        "dob": DOB,
        "city": city,
        "state": state,
        "country": country
    }


    try:
        #insert the obtained details into mongo db
        response=collection.insert_one(document)
        print(response)
        # pass the content dynamically to html page ( where we can edit and delete buttons available for further action)
        return templates.TemplateResponse('show_details.html', {"request": request, "document": document})
    except HTTPException as e:
        return templates.TemplateResponse('error_display.html',{'status_code':e.status_code,'detail':e.detail,'request':request})
    except Exception as e:
        return templates.TemplateResponse('error_display.html',{'status_code':500,'detail':'Internal Server Error','request':request})

### list_all_documents
@app.get("/list_documents")
async def list(request: Request):
    try:
        list_of_docs = await collection.find().to_list(length=None)
        return templates.TemplateResponse('list_documents.html', {'request':request, "document": list_of_docs})

    except HTTPException as e:
        return templates.TemplateResponse('error_display.html',{'status_code':e.status_code,'detail':e.detail,'request':request})
    except Exception as e:
        return templates.TemplateResponse('error_display.html',{'status_code':500,'detail':'Internal Server Error','request':request})
### delete a particular document
@app.post("/delete/{document_id}")
async def delete(request:Request,document_id:str):
    try:
        id=ObjectId(document_id)
        await collection.delete_one({"_id":id})
        return  templates.TemplateResponse('message_after_edit.html',{'request':request,'message':'The record has been deleted'})
    except HTTPException as e:
        return templates.TemplateResponse('error_display.html',{'status_code':e.status_code,'detail':e.detail,'request':request})
    except Exception as e:
        return templates.TemplateResponse('error_display.html',{'status_code':500,'detail':'Internal Server Error','request':request})

### edit a particular document
@app.get("/edit/{document_id}")
async def edit(request:Request,document_id:str):
    try:
        id=ObjectId(document_id)
        data=await collection.find_one({"_id":id})
        if data:
            data_to_be_prefilled={
                "fname":data.get('first_name',''),
                "lname":data.get('last_name',''),
                "DOB":data.get('dob',''),
                "city":data.get('city',''),
                "state":data.get('state',''),
                "country":data.get('country',''),
            }
        return templates.TemplateResponse('registration.html',{'request':request,"data":data_to_be_prefilled,"id":id})
    except HTTPException as e:
        return templates.TemplateResponse('error_display.html',{'status_code':e.status_code,'detail':e.detail,'request':request})
    except Exception as e:
        return templates.TemplateResponse('error_display.html',{'status_code':500,'detail':'Internal Server Error','request':request})

#uvicorn.run(app, host="127.0.0.1", port=8000)




