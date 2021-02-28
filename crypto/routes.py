from crypto import app
from flask import render_template, request, redirect, url_for
from crypto.forms import PurchaseForm
import datetime
import sqlite3
import json
import requests
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

BBDD = './data/CryptoData.db'
API_KEY=app.config['API_KEY']

cryptos = ("BTC", "ETH", "XRP", "LTC", "BCH", "BNB", "USDT", "EOS", "BSV", "XLM", "ADA", "TRX")

def api(cryptoFrom, cryptoTo):

    url= "https://pro-api.coinmarketcap.com/v1/tools/price-conversion?amount=1&symbol={}&convert={}&CMC_PRO_API_KEY=<API_KEY>".format(cryptoTo, cryptoFrom)

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': API_KEY
    }

    session = Session()
    session.headers.update(headers)

    response = session.get(url)
    data = json.loads(response.text)
    try:
        return ('', data['data']['quote'][cryptoFrom]['price'])
    except:
        errorCodeAPI = data['status']['error_code']
        return ('error', errorCodeAPI)

def ApiErrors(codigo):
    if codigo == 1001:
        msg = "La API KEY no es válida"
    elif codigo == 1002:
        msg= "No existe API KEY"
    elif codigo == 1003:
        msg= "La API KEY no está activada"
    elif codigo == 1004:
        msg= "La API KEY ha caducado"
    elif codigo == 1005:
        msg= "Se requiere API KEY"
    elif codigo == 1006:
        msg= "API KEY incompatible con esta operación"
    elif codigo == 1007:
        msg= "API KEY deshabilitada"
    elif codigo == 1008:
        msg= "Excedido límite de velocidad de solicitud HTTP de la API KEY"
    elif codigo == 1009:
        msg= "Excedido límite de tarifa diaria de API KEY"
    elif codigo == 1010:
        msg= "Excedido límite de tarifa mensual de API KEY"
    elif codigo == 1011:
        msg= "Alcanzado límite de velocidad de la IP"

    return msg

def dataQuery(consulta):

    conex = sqlite3.connect(BBDD)
    cursor = conex.cursor()

    movs = cursor.execute(consulta).fetchall()

    if len(movs) == 0:
        movs = None

    conex.commit()
    conex.close()

    return movs

def cryptoSaldo():
    cryptoBalance = []
    for coin in cryptos:
        cryptoBalanceCoin = dataQuery('''
                                WITH BALANCE
                                AS
                                (
                                SELECT SUM(to_quantity) AS saldo
                                FROM MOVEMENTS
                                WHERE to_currency LIKE "%{}%"
                                UNION ALL
                                SELECT -SUM(from_quantity) AS saldo
                                FROM MOVEMENTS
                                WHERE from_currency LIKE "%{}%"
                                )
                                SELECT SUM(saldo)
                                FROM BALANCE
                                '''.format(coin, coin))
        if cryptoBalanceCoin[0] == (None,):
            cryptoBalanceCoin=0
            cryptoBalance.append(cryptoBalanceCoin)
        else:
            cryptoBalance.append(cryptoBalanceCoin[0][0])
    return cryptoBalance

@app.route("/")
def index():
        try:
            registros = dataQuery("SELECT date, time, from_currency, from_quantity, to_currency, to_quantity FROM MOVEMENTS;")
            return render_template("index.html", menu='index', registros = registros)

        except sqlite3.Error:
            registros = None
            errorDB = "ERROR EN BASE DE DATOS, INTENTE EN UNOS MINUTOS"
            return render_template("index.html", menu='index', errorDB=errorDB, registros=registros)

@app.route("/purchase", methods=['GET', 'POST'])
def purchase():

    form = PurchaseForm(request.form)
    slctFrom=request.values.get("slct_from")
    slctTo=request.values.get("slct_to")
    units=request.values.get("inputCantidad")
    quant = 0
    pu = 0

    if request.method == 'GET':

        return render_template("purchase.html", menu='purchase', form=form, data=[quant,pu])

    if request.values.get("submitCalcular"):
        if not form.validate():
            quant = 0
            pu = 0
            validError = "OPERACIÓN INCORRECTA - LA CANTIDAD DEBE SER NUMÉRICA Y SUPERIOR A 0"
            return render_template("purchase.html", menu='purchase',form=form , validError=validError, data=[quant,pu])

        # Validacion de monedas distintas

        if slctFrom == slctTo:
            quant = 0
            pu = 0
            cryptoError = "OPERACIÓN INCORRECTA - DEBE ELEGIR DOS MONEDAS DISTINTAS"
            return render_template("purchase.html", menu='purchase',form=form , cryptoError=cryptoError, data=[quant,pu])

        # Validacion de compatibilidad de calculo entre criptomendas

        if slctFrom == 'EUR' and slctTo != 'BTC':
            quant = 0
            pu = 0
            cryptoIncompatible = "OPERACIÓN INCORRECTA - NO PUEDE COMPRAR {} CON EUROS".format(slctTo)
            return render_template("purchase.html", menu='purchase',form=form , cryptoIncompatible=cryptoIncompatible, data=[quant,pu])

        if slctTo == 'EUR'and slctFrom != "BTC":
            quant = 0
            pu = 0
            cryptoIncompatible = "OPERACIÓN INCORRECTA - NO PUEDE COMPRAR EUROS CON {}".format(slctFrom)
            return render_template("purchase.html", menu='purchase', form=form , cryptoIncompatible=cryptoIncompatible, data=[quant,pu])

        apiConsult = api(slctFrom, slctTo)
        if apiConsult[0] =='error':
            quant = 0
            pu = 0
            messageError = ApiErrors(apiConsult[1])
            errorAPI = "ERROR EN API - {}".format(messageError)
            return render_template("purchase.html", menu='purchase', form=form , errorAPI=errorAPI, data=[quant,pu])
        else:
            dataQuant = apiConsult[1]

        quant = float(dataQuant)*float(units)
        pu = dataQuant

        return render_template("purchase.html", menu='purchase', form=form, data=[quant, pu, slctFrom])

    if request.values.get("submitCompra"):

        if not form.validate():
            quant = 0
            pu = 0
            validError = "OPERACIÓN INCORRECTA - LA CANTIDAD DEBE SER NUMÉRICA Y SUPERIOR A 0"
            return render_template("purchase.html", menu='purchase', form=form , validError=validError, data=[quant,pu])

        # Validacion de monedas distintas

        if slctFrom == slctTo:
            quant = 0
            pu = 0
            cryptoError = "OPERACIÓN INCORRECTA - DEBE ELEGIR DOS MONEDAS DISTINTAS"
            return render_template("purchase.html", menu='purchase', form=form , cryptoError=cryptoError, data=[quant,pu])

        # Validacion de compatibilidad de compra entre criptomendas

        if slctFrom == 'EUR' and slctTo != 'BTC':
            quant = 0
            pu = 0
            cryptoIncompatible = "OPERACIÓN INCORRECTA - NO PUEDE COMPRAR {} CON EUROS".format(slctTo)
            return render_template("purchase.html", menu='purchase', form=form , cryptoIncompatible=cryptoIncompatible, data=[quant,pu])

        if slctTo == 'EUR'and slctFrom != "BTC":
            quant = 0
            pu = 0
            cryptoIncompatible = "OPERACIÓN INCORRECTA - NO PUEDE COMPRAR EUROS CON {}".format(slctFrom)
            return render_template("purchase.html", menu='purchase', form=form , cryptoIncompatible=cryptoIncompatible, data=[quant,pu])

        #Calculo de saldo de la moneda con la que se quiere comprar
        if slctFrom == 'EUR':
            saldo = 9999999999
        else:
            try:
                saldoStr = dataQuery('''
                            WITH BALANCE
                            AS
                            (
                            SELECT SUM(to_quantity) AS saldo
                            FROM MOVEMENTS
                            WHERE to_currency LIKE "%{}%"
                            UNION ALL
                            SELECT -SUM(from_quantity) AS saldo
                            FROM MOVEMENTS
                            WHERE from_currency LIKE "%{}%"
                            )
                            SELECT SUM(saldo)
                            FROM BALANCE;
                            '''.format(slctFrom, slctFrom))
            except sqlite3.Error:
                quant = 0
                pu = 0
                errorDB = "ERROR EN BASE DE DATOS, INTENTE EN UNOS MINUTOS"
                return render_template("purchase.html", menu='purchase', form=form , errorDB=errorDB, data=[quant,pu])

            if saldoStr[0] == (None,):
                saldo = 0
            else:
                saldo = saldoStr[0][0]

        if slctFrom == 'EUR' or saldo != 0:

            dt = datetime.datetime.now()
            fecha=dt.strftime("%d/%m/%Y")
            hora=dt.strftime("%H:%M:%S")
            apiConsult = api(slctFrom, slctTo)
            if apiConsult[0] =='error':
                quant = 0
                pu = 0
                messageError = ApiErrors(apiConsult[1])
                errorAPI = "ERROR EN API - {}".format(messageError)
                return render_template("purchase.html", menu='purchase', form=form , errorAPI=errorAPI, data=[quant,pu])
            else:
                dataQuant = apiConsult[1]
                quant = float(dataQuant)*float(units)

            # Comprobación de saldo suficiente con la crypto que se quiere comprar

            if saldo >= quant or slctFrom == 'EUR':

                conex = sqlite3.connect(BBDD)
                cursor = conex.cursor()
                mov = "INSERT INTO MOVEMENTS(date, time, from_currency, from_quantity, to_currency, to_quantity) VALUES(?, ?, ?, ?, ?, ?);"

                try:
                    cursor.execute(mov, (fecha, hora, slctFrom, float(quant), slctTo, float(units)))
                except sqlite3.Error:
                    quant = 0
                    pu = 0
                    errorDB = "ERROR EN BASE DE DATOS, INTENTE EN UNOS MINUTOS"
                    return render_template("purchase.html", menu='purchase', form=form , errorDB=errorDB, data=[quant,pu])

                conex.commit()
                try:
                    registros = dataQuery("SELECT date, time, from_currency, from_quantity, to_currency, to_quantity FROM MOVEMENTS;")
                    conex.close()
                    return render_template("index.html", menu='index', form=form, registros=registros)
                except sqlite3.Error:
                    quant = 0
                    pu = 0
                    errorDB = "ERROR EN BASE DE DATOS, INTENTE EN UNOS MINUTOS"
                    return render_template("purchase.html", menu='purchase', form=form , errorDB=errorDB, data=[quant,pu])
            else:
                pu = dataQuant
                sinSaldo = "NO TIENE SALDO SUFICIENTE EN {} PARA REALIZAR ESTA OPERACIÓN".format(slctFrom)
                return render_template("purchase.html", menu='purchase', form=form , sinSaldo=sinSaldo, data=[quant,pu])
        else:
            quant = 0
            pu = 0
            alert = "NO EXISTE SALDO DE COMPRA EN LA CRYPTOMONEDA {}".format(slctFrom)
            return render_template("purchase.html", menu='purchase', form=form, data=[quant, pu, slctFrom], alert=alert)

@app.route("/status")
def inverter():

    # Calculo Inversion
    try:
        movOrNot = dataQuery("SELECT date, time, from_currency, from_quantity, to_currency, to_quantity FROM MOVEMENTS;")
    except sqlite3.Error:
        totalInver = 0
        valorAct = 0
        dif = 0
        errorDB = "ERROR EN BASE DE DATOS, INTENTE EN UNOS MINUTOS"
        return render_template("status.html", menu='status', errorDB=errorDB, movOrNot=True)

    if movOrNot == None:
        return render_template("status.html", menu='status', movOrNot=True)

    try:
        InverFrom= dataQuery('SELECT SUM(from_quantity) FROM MOVEMENTS WHERE from_currency LIKE "%EUR%";')
        InverTo= dataQuery('SELECT SUM(from_quantity) FROM MOVEMENTS WHERE to_currency LIKE "%EUR%";')
    except sqlite3.Error:
        totalInver = 0
        valorAct = 0
        dif = 0
        errorDB = "ERROR EN BASE DE DATOS, INTENTE EN UNOS MINUTOS"
        return render_template("status.html", menu='status', errorDB=errorDB, movOrNot=True)

    totalInverFrom = 0
    totalInverTo = 0
    for x in range(len(InverFrom)):
        if InverFrom[x] == (None,):
            totalInverFrom += 0
        else:
            InverFromInt = InverFrom[x][0]
            totalInverFrom += InverFromInt

    for x in range(len(InverTo)):
        if InverTo[x] == (None,):
            totalInverTo += 0
        else:
            InverToInt = InverTo[x][0]
            totalInverTo += InverToInt

    totalInver = totalInverFrom + totalInverTo

    # Calculo saldo de Cryptomonedas
    try:
        cryptoSaldo()
    except sqlite3.Error:
        totalInver = 0
        valorAct = 0
        dif = 0
        errorDB = "ERROR EN BASE DE DATOS, INTENTE EN UNOS MINUTOS"
        return render_template("status.html", menu='status', errorDB=errorDB, movOrNot=True)

    # Calculo Valor Actual de todas las cryptomonedas en Euros y totalizarlas en Status
    xi = 0
    cryptoValorActual = {}
    valorAct = 0
    for coin in cryptos:
        apiConsult = api('EUR',coin)
        if apiConsult[0] =='error':
            totalInver = 0
            valorAct = 0
            dif = 0
            messageError = ApiErrors(apiConsult[1])
            errorAPI = "ERROR EN API - {}".format(messageError)
            return render_template("status.html", menu='status', errorAPI=errorAPI, totalInver=totalInver, cryptoBalance=cryptoSaldo(), valorAct=valorAct, dif=dif)
        else:
            cotizacion = apiConsult[1]
            saldoCoin = cryptoSaldo()[xi]
            cryptoValorActual[coin] = cotizacion * saldoCoin
            valorAct += cryptoValorActual[coin]
            xi += 1

    # Calculo Beneficio/Perdida
    dif = valorAct - totalInver

    return render_template("status.html", menu='status', totalInver=totalInver, cryptoBalance=cryptoSaldo(), valorAct=valorAct, dif=dif)