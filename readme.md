# PROYECTO FLASK CONVERSOR DE MONEDAS
## INSTALACIÓN

### ACTIVAR ENTORNO VIRTUAL

Primero tenemos que crear el entorno virtual, con el siguiente codigo nos creamos el entorno virtual:
````
python3 -m venv venv
````

Para poder activar el entorno virtual, tenemos que meter el codigo: 
````
source venv/bin/activate 
. venv/bin/activate
````

### INSTALAR REQUIREMENTS.TXT
````
pip install -r requirements.txt
````
### OBTENCION DE API COINMARKET

Para ejecutar el programa se requiere la API de la siguienet pagina https://coinmarketcap.com/. Es necesario obtener una API KEY que deberá incluirse en el fichero config_templates.py

### CREACIÓN DE BASE DE DATOS

Para la creación de la BBDD, tendrá que bajarse un programa para la gestion  de BBDD.
En este caso puede decargarse, SQLite DB Browser.

### FICHERO CONFIG

Renombrar el fichero "config_templates.py" por "config.py" e incluir la siguiente documentacion:

SECRET_KEY="Poner aqui su clave secreta"
API_KEY="Poner aquí su API KAY de Coinmarket"



