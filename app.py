from flask import *

from flask_pymongo import PyMongo

from flask_bootstrap import Bootstrap

from datetime import datetime

from flask_moment import Moment

import pandas_datareader as pdr
import pandas as pd

import requests

app = Flask('my-stock')

app.config['SECRET_KEY'] = 'sOtCk!'

app.config['MONGO_URI'] = 'mongodb://localhost:27017/my-stock-db'

monent = Moment(app)

Bootstrap(app)

mongo = PyMongo(app)

weather_api = 'c115e005de28c13c6e9ff0ad6d7b14ca'

def stock_market():
    current = datetime.now().strftime("%Y-%m-%d")
    dowjone = pdr.get_data_yahoo('^DJI', start=current, end=current)['Adj Close']
    dowjone = pd.Series(dowjone[current])
    dow = [x for x in dowjone][0]

    nasd = pdr.get_data_yahoo('^IXIC', start=current, end=current)['Adj Close']
    nasd = pd.Series(nasd[current])
    nas = [x for x in nasd][0]
    stk = [round(dow,5), round(nas,5)]
    return stk

def weather():
    response = requests.get("http://ip-api.com/json/")
    js = response.json()
    city = js['city']

    api = 'c115e005de28c13c6e9ff0ad6d7b14ca'
    api_address = 'http://api.openweathermap.org/data/2.5/weather?appid=' + api + '&q='

    url = api_address + city + '&units=imperial'

    data = requests.get(url).json()
    temp = data['main']['temp']

    humidity = data['main']['humidity']

    wea = data['weather'][0]['main']

    des = data['weather'][0]['description']

    weather_list = [temp,humidity, wea,des]

    return weather_list


@app.route('/', methods = ['GET','POST'])
def register():
    session.pop('user-info', None)
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        doc = {}
        user = mongo.db.users.find({})
        for item in request.form:
            doc[item] = request.form[item]
        user_list= []
        for u in user:
            print(u)
            user_list.append(u['email'])
        print(user_list)
        if doc['email'] in user_list:
            flash( doc['email']+' already registered')
            return redirect('/')
        mongo.db.users.insert_one(doc)

        flash('Account created successfullu!')
        return redirect('/login')

@app.route('/login', methods =['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        doc = {'email':request.form['email'],'password':request.form['password']}

        found = mongo.db.users.find_one(doc)
        if found is None:
            flash('user name and password you entered did not match our record. Please check it again')
            return redirect('/login')
        else:
            lst = weather()
            stk_list = stock_market()
            session['user-info'] = {'firstname':found['firstname'],'lastname':found['lastname'], 'email':found['email'],'loginTime': datetime.utcnow(),
                                    'temp':lst[0],'hum':lst[1], 'weather':lst[2], 'dow':stk_list[0], 'nas':stk_list[1]}
            return redirect('/stock')

@app.route('/stock', methods=['GET','POST'])
def stock():
    total = 0

    if 'user-info' in session:
        userinfo = mongo.db.entries.find({'user':session['user-info']['email']})
        if request.method == 'GET':

            savelogin = mongo.db.entries.find({'user':session['user-info']['email']})
            for entry in savelogin:
                total = total + entry['total']
            total = round(total,2)
            savelogin = mongo.db.entries.find({'user': session['user-info']['email']})
            return render_template('stock.html', entries=savelogin, total = total)
        elif request.method == 'POST':
            edit = 'non'
            user = mongo.db.entries.find({'user': session['user-info']['email']})
            entry = {}
            entry['user'] = session['user-info']['email']
            share = request.form['share']
            tick = request.form['tick']
            act = request.form['action']
            print(act)
            current = datetime.utcnow().strftime("%Y-%m-%d")
            ticker = pdr.get_data_yahoo(tick.upper(), start=current, end=current)['Adj Close']
            ticker = pd.Series(ticker[current])
            price = [x for x in ticker][0]

            share = int(share)
            print(user.count())
            count = 0
            for u in user:
                u_share = int(u['share'])
                if u['tick'] == tick:
                    if act == 'Buy':
                        share = u_share + share
                        edit = 'edit'
                    elif act == 'Sell':
                        print(u_share, share)
                        if u_share > share:
                            share = u_share - share
                            edit = 'edit'
                        elif u_share < share:
                            flash('out of your balance ')
                        elif u_share == share:
                            edit = 'delete'
                    break
                count += 1

            if count == user.count():
                edit = 'insert'


            entry['tick'] = tick

            entry['share'] = share
            entry['price'] = round(price,3)

            total = round(int(share) * price, 3)
            entry['total'] = total
            entry['time'] = datetime.utcnow()

            #entry ={'user':session['user-info']['email'],'content':request.form['content'],'time':datetime.utcnow()}
            if edit == 'edit':
                mongo.db.entries.update_one({'tick': entry['tick']},{ '$set':{'share': entry['share'],'total' : entry['total'], 'time': entry['time']}})
            elif edit == 'insert':
                mongo.db.entries.insert_one(entry)
            elif edit == 'delete':
                mongo.db.entries.remove({'tick':entry['tick']})
            return redirect('/stock')
    else:
        flash('You need to login first')
        return redirect('/login')

@app.route('/logout')
def logout():
    # removing user information from the session
        session.pop('user-info', None)
        return redirect('/login')

app.run(debug='True')