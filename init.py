import os
import boto3
import sys
import pymysql

client=boto3.client("ssm",region_name="us-east-1")

def get_param(name):
    return client.get_parameter(
        Name=f"/application/banking/{name}",
        WithDecryption=True
    )["Parameter"]["Value"]

try:
    conn=pymysql.connect(
        host=get_param("DB_HOST"),
        port=int(get_param("DB_PORT")),
        user=get_param("DB_USER"),
        password=get_param("DB_PASSWORD"),
        connect_timeout=10,
    )

    cur=conn.cursor()

    base_dir=os.path.dirname(os.path.abspath(__file__))
    sql_file=os.path.join(base_dir,"init.sql")

    with open(sql_file,"r",encoding="utf-8") as f:
        sql=f.read()

    for statement in sql.split(";"):
        statement=statement.strip()
        if statement:
            cur.execute(statement)
    
    conn.commit()
    print("✅ Database connected successfully")

except Exception as e:
    print("Error :",e)
    sys.exit(1)

finally:
    conn.close()