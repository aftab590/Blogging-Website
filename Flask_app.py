from flask import Flask,render_template, request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail
import json
import os
import math
import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np
from datetime import datetime


local_server = True
with open('Flask\config.json','r') as com:
    params = json.load(com)["params"]

app = Flask(__name__)
app.secret_key= 'its-a-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']

app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']

)
mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

class Contacts(db.Model):
    #sno,name,email,msg,date,phone
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    msg = db.Column(db.String(40), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    phone = db.Column(db.String(12), nullable=False)

class Posts(db.Model):
    
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)
    


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last_page = math.ceil(len(posts)/int(params['no_of_posts']))

    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']): (page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])] # posts = posts[0:2]

    #Pagination Logic..
    if (page==1):
        prev = "#"
        next = "/?page="+ str(page+1)
    elif(page==last_page):
        prev = "/?page="+ str(page-1)
        next= "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)

    return render_template('index.html',params = params, posts = posts, prev=prev, next=next,last = last_page,page=page)



@app.route("/about")
def about():
    return render_template('about.html',params = params)

@app.route("/analysis")
def analysis():
    
    objects = ('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')
    val = len(objects)
    
    performance_1 = [2,0,3,1,0,6,2]
    performance_2 = [1,6,0,2,1,2,5]
    p1= sum(performance_1)
    p2= sum(performance_2)
    fig, ax = plt.subplots()
    y_pos = np.arange(val)
    bar_width = 0.35
    opacity = 0.8

    rects1 = plt.bar(y_pos, performance_1, bar_width,
    alpha=opacity,
    color='b',
    label='2 weeks before')

    rects2 = plt.bar(y_pos + bar_width, performance_2, bar_width,
    alpha=opacity,
    color='g',
    label='1 week before')

    # plt.bar(y_pos, performance_1, align='center', alpha=0.5)
    plt.xticks(y_pos + bar_width, objects)
    plt.xlabel('Week Days')
    plt.ylabel('Posts Added')
    plt.legend()
    plt.tight_layout() 
    # plt.title('Analysis of added posts')
    plt.savefig('Flask/static/img/plot1.png')

    avg_posts_2 = round(p1/7)
    avg_posts_1 = round(p2/7)

    incre = 1 - (p1/p2)
    decre = (p1/p2)-1
    incre = round(incre,2)
    decre = round(decre,2)

    return render_template('analysis.html', url='/static/img/plot1.png', params=params,avg_posts_2=avg_posts_2,avg_posts_1=avg_posts_1,incre=incre,decre=decre,p1=p1,p2=p2)


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)


    if request.method=='POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if(username == params['admin_user'] and userpass == params['admin_password']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)
 
    return render_template('login.html',params = params)

@app.route("/edit/<string:sno>",methods = ['GET','POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if sno == '0':
                post = Posts(title=box_title,slug=slug,content=content,tagline=tline,img_file=img_file,date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug=slug
                post.content= content
                post.tagline= tline
                post.img_file= img_file
                post.date = date
                db.session.commit()
                # return redirect('/edit/'+sno)
                return redirect('/dashboard')

        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html',params=params,post=post,sno=sno)



@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:sno>",methods = ['GET','POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


@app.route("/contact",methods = ['GET','POST'])
def contact():
    if(request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name,phone=phone,email=email,date=datetime.now(),msg=message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message("New Message From " + name,
                            sender=email,
                            recipients=[params['gmail-user']],
                            body = message + "\nContact: " + phone
                            )

    return render_template('contact.html',params = params)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params = params, post=post)

app.run(debug= True)