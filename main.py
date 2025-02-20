from flask import Flask,render_template,request,session,redirect,flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import json,os,math

with open('config.json','r') as c:
    params = json.load(c)["params"]  # json.loads() function is used to parse a JSON string and convert it into a Python object

local_server = True
app = Flask(__name__)
app.secret_key = 'secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_url']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_url']


db = SQLAlchemy(app) # initialize


class Contacts(db.Model):
    '''sno name email ph_no msg date'''
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable = False) # nullable means this text cannot be empty
    email = db.Column(db.String(20), nullable = False)
    ph_no = db.Column(db.String(12), nullable = False)
    msg = db.Column(db.String(120), nullable = False)
    date = db.Column(db.String(12), nullable = True)

class Posts(db.Model):
    '''sno title slug content date'''
    sno = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(80), nullable = False)
    slug = db.Column(db.String(20), nullable = False)
    content = db.Column(db.String(), nullable = False)
    date = db.Column(db.String(12), nullable = True)
    img_file = db.Column(db.String(12), nullable = True)

@app.route("/")
def home():
    flash("Welcome To Blog Post","info")
    # Pagination Logic

    # Fetching All Posts
    posts = Posts.query.filter_by().all()  # [0:params['no_of_posts']]

    # Calculating total number of pages:
    last = math.ceil(len(posts)/int(params['no_of_posts']))

    # it’s important to get on what page user is.
    page = request.args.get('page',1)

    # Ensure page is a valid integer
    try:
        page = int(page)
    except ValueError:
        page = 1  # Default to page 1 if not a valid number

    posts=posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts']) + int(params['no_of_posts'])]

    prev = f"/?page={page - 1}" if page > 1 else None
    nxt = f"/?page={page + 1}" if page < last else None

    return render_template('index.html',params = params,posts=posts,prev=prev,next=nxt)

@app.route("/about")
def about():
    return render_template('about.html',params = params)

@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            box_title = request.form.get('title')
            box_slug = request.form.get('slug')
            box_content = request.form.get('content')
            box_img_file = request.form.get('img_file')
            date = datetime.now()

            if sno == '0':  # New post
                post = Posts(title=box_title, slug=box_slug, content=box_content, img_file=box_img_file, date=date)
                db.session.add(post)
                db.session.commit()
                flash("New Post Add Successfully",'success')

            else:  # Edit existing post
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = box_slug
                post.content = box_content
                post.img_file = box_img_file
                post.date = date
                db.session.commit()
                flash("Post Edit Success","success")

            return redirect('/dashboard')  # Redirect to dashboard instead of refreshing edit page

    post = None if sno == '0' else Posts.query.filter_by(sno=sno).first()
    return render_template('edit.html', params=params, post=post)

@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            f = request.files['file1']
            if f.filename == '':
                flash("No selected file", "danger")
                return redirect(request.url)
            try:
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
                flash("File uploaded successfully!", "success")
            except Exception as e:
                flash("File upload failed!", "danger")
            return redirect(request.url)

    return redirect("/dashboard")

@app.route("/dashboard",methods = ['GET','POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html',params = params,posts = posts)

    if request.method=='POST':
        username = request.form.get('username')
        userpass = request.form.get('password')
        if (username == params['admin_user'] and userpass == params['admin_pass']):
            # set the session variable , We want to set up session variable because we don’t want our user to login again and again, that would be too inconvenient.
            # To set up session variable, we first have to import session from flask. So, simply import it.
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html',params = params,posts = posts)

    # redirect to admin panel
    return render_template('login.html',params = params)

@app.route("/post/<string:post_slug>",methods = ['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params = params,post = post)

@app.route("/contact", methods = ['GET','POST'])
def contact():
    if(request.method=='POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name,email=email,ph_no=phone,msg=message,date=datetime.now())
        db.session.add(entry)
        db.session.commit()

        flash("Thanks for send your details,We will get back to you soon","success")
    return render_template('contact.html',params = params)

@app.route("/delete/<string:sno>",methods=['GET','POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    flash("Delete Post Success!","danger")
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')


# Make User Authentication

@app.route('/register' , methods=['POST','GET'])
def register():
    if request.method=='POST':
        pass
    return render_template('register.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        pass
    return render_template('login.html')

app.run(debug=True)
