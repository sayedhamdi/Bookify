""" this file is made to migrate books from books.csv to data base"""
import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
#connect to db
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
#nhel el fichier
def main():
	file=open("./books.csv")
	books = csv.reader(file)
	print(books)
	for isbn,title,author,year in books:
		db.execute("INSERT INTO books (isbn,title,author,year) VALUES(:isbn,:title,:author,:year)",{"isbn":isbn,"title":title,"author":author,"year":year})
		print("added bookisbn : {isbn} titled {title} from the author {author} released in {year}")
		db.commit()


if __name__=="__main__":
	main()
