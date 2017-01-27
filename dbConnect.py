import pymysql

def connection():
    conn = pymysql.connect(host="localhost",
                           user="root",
                           password="gamblers",
                           db="Recruiter")

    c = conn.cursor()
    return c, conn                       
