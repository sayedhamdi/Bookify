import os
import requests
from flask import Flask, session,render_template,request,redirect,url_for,jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_bcrypt import Bcrypt
import requests


app = Flask(__name__)
bcrypt = Bcrypt(app)
# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
   
    return render_template("index.html")



@app.route("/register" ,methods=["POST","GET"])
def register():
	error=""
	if request.method =="POST":
		email=request.form.get("email")
		db_email = db.execute("select email from users where email=:email",{"email":email}).fetchone()
		if (db_email is None):
			name=request.form.get("name")
			password=request.form.get("password")
			db.execute("INSERT INTO users(name,email,password) VALUES(:name,:email,:password)",{'name':name,'email':email,'password':password})
			db.commit()
			return redirect(url_for("login"))
		else:
			error = "the email already exists"
	return render_template("register.html",error=error)


@app.route("/login",methods=["POST","GET"])
def login():
	if request.method=="POST":
		email = request.form.get("email")
		password = request.form.get("password")
		#get password from database
		row=db.execute("SELECT id,password, name FROM users WHERE email=:email",{'email':email}).fetchone()
		db.commit()
		user_id=row[0]
		pwd=row[1]
		username=row[2]
		verif = (pwd==password)
		if verif:
			session['logged']=True
			session['username']=username
			session['user_id']=user_id
			return redirect(url_for("index"))
		else:
			error = "password incorrect"
			render_template("login.html",error=error)
	return render_template("login.html")

@app.route("/book/<int:id>")
def book(id):
    user_id=session["user_id"]
    has_commented=bool(db.execute("SELECT * from reviews where user_id=:user_id AND book_id=:id",{"user_id":user_id,"id":id}).fetchone())
    comments=db.execute("SELECT * FROM reviews WHERE book_id = :id",{"id":id})
    book=db.execute("SELECT * from books WHERE id=:id",{"id":id}).fetchone()
    db.commit()
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "S4HGQaqJnoxjGE9vJynWA", "isbns":book[1]})
    if res.status_code!=200:
		res = "Couldn't find rating on good reads"
    else :
    	res= res.json()["books"][0].get("average_rating")
    return render_template("book.html",book=book,has_commented=has_commented,comments=comments,good_read=res)
	
@app.route("/reviews/<int:id>",methods=["POST"])
def reviews(id):
    if session["logged"]:
	    user_id=session["user_id"]
    if request.method=="POST":
		rate = request.form.get("rate")
		comment=request.form.get("comment")
		
		db.execute("INSERT INTO reviews(rate,user_id,book_id,comment) VALUES(:rate,:user_id,:book_id,:comment)",{'rate':rate,'user_id':user_id,'book_id':id,'comment':comment})
		db.commit()
		return redirect(url_for("book",id=id))


@app.route("/users")
def users():
	users = db.execute("select * from users")
	return render_template("users.html",users=users)

@app.route("/logout")
def logout():
	session["logged"]=False
	session["username"]=""
	return redirect(url_for("index"))

@app.route("/search",methods=["POST","GET"])
def search():
    logged=session["logged"]
    username=""
    if session["logged"]:
        username = session["username"]
	if request.method=="POST":
		search = request.form.get("search")
		row=db.execute("""SELECT * FROM books WHERE UPPER(isbn) LIKE UPPER(:search) OR UPPER(title) LIKE UPPER(:search) OR UPPER(author) LIKE UPPER(:search)""",{'search':"%"+search+"%"}).fetchall()
		db.commit()
		return render_template("search.html",books=row,username=username,logged=logged)
	return render_template("search.html")


@app.route("/api/<string:isbn>")
def api(isbn):
	book = db.execute("select * from books where isbn = :isbn",{"isbn":isbn}).fetchone()
	if book is None:
		return jsonify({"error":"invalid isbn"}),422
	id=book[0]
	title=book[2]
	author=book[3]
	year=book[4]
	review=db.execute("SELECT  AVG(rate),COUNT(*) from reviews WHERE book_id =:id",{"id":id}).fetchone()
	avgerage_score = round(review[0],2)
	review_count= review[1]
	
	return jsonify({
					 "title": title,
    				 "author": author,
    				 "year": year,
    				 "isbn": isbn,
					 "review_count":review_count,
					 "average_score":avgerage_score			
	})