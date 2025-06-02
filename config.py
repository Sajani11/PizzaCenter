import os

class Config:
   
    SECRET_KEY = 'sajani1213xyz'

    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'diskastra123xyz@@SA'
    MYSQL_DB = 'pizzadb'


    UPLOAD_FOLDER = os.path.join('static', 'pizza_images')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    