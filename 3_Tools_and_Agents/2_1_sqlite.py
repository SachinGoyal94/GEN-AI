#creating a database so that a user can chat with it

import sqlite3
connection=sqlite3.connect('students.db')
cursor=connection.cursor()

cursor.execute('''drop table Student''')
table_info="""
create table Student(Name Varchar(25),class Varchar(25),Roll_no INT)
"""
cursor.execute(table_info)

cursor.execute(''' insert into Student values ("Rohan","12",1)''')
cursor.execute(''' insert into Student values ("Mohit","12",2)''')
cursor.execute(''' insert into Student values ("James","12",3)''')
cursor.execute(''' insert into Student values ("John","12",4)''')

print("the inserted records are:")
data=cursor.execute('''select * from Student''')
for row in data:
    print(row)

connection.commit()
connection.close()