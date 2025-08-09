from flask import Flask, render_template, request
from pymysql import connections
import os
import random
import argparse

app = Flask(__name__)

# Environment variables with defaults
DBHOST = os.environ.get("DBHOST", "localhost")
DBUSER = os.environ.get("DBUSER", "root")
DBPWD = os.environ.get("DBPWD", "password")
DATABASE = os.environ.get("DATABASE", "employees")
DBPORT = int(os.environ.get("DBPORT", 3306))
APP_COLOR = os.environ.get("APP_COLOR", "lime")

# Supported color mapping
color_codes = {
    "red": "#e74c3c",
    "green": "#16a085",
    "blue": "#89CFF0",
    "blue2": "#30336b",
    "pink": "#f4c2c2",
    "darkblue": "#130f40",
    "lime": "#C1FF9C",
}
SUPPORTED_COLORS = ", ".join(color_codes.keys())
COLOR = color_codes.get(APP_COLOR, "#C1FF9C")

# DB connection
try:
    db_conn = connections.Connection(
        host=DBHOST, port=DBPORT, user=DBUSER, password=DBPWD, db=DATABASE
    )
except Exception as e:
    print("ERROR: Could not connect to MySQL database.")
    print(e)
    exit(1)

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('addemp.html', color=COLOR)

@app.route("/about", methods=['GET'])
def about():
    return render_template('about.html', color=COLOR)

@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    primary_skill = request.form['primary_skill']
    location = request.form['location']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    try:
        cursor.execute(insert_sql, (emp_id, first_name, last_name, primary_skill, location))
        db_conn.commit()
        emp_name = f"{first_name} {last_name}"
    except Exception as e:
        print(f"ERROR while inserting employee: {e}")
        emp_name = "Error occurred"
    finally:
        cursor.close()

    return render_template('addempoutput.html', name=emp_name, color=COLOR)

@app.route("/getemp", methods=['GET'])
def GetEmp():
    return render_template("getemp.html", color=COLOR)

@app.route("/fetchdata", methods=['POST'])
def FetchData():
    emp_id = request.form['emp_id']
    select_sql = "SELECT emp_id, first_name, last_name, primary_skill, location FROM employee WHERE emp_id=%s"
    cursor = db_conn.cursor()
    output = {}

    try:
        cursor.execute(select_sql, (emp_id,))
        result = cursor.fetchone()
        if result:
            output = {
                "emp_id": result[0],
                "first_name": result[1],
                "last_name": result[2],
                "primary_skills": result[3],
                "location": result[4]
            }
        else:
            return "No employee found with the given ID."
    except Exception as e:
        print(f"ERROR while fetching employee: {e}")
        return "Error fetching data."
    finally:
        cursor.close()

    return render_template("getempoutput.html",
                           id=output["emp_id"],
                           fname=output["first_name"],
                           lname=output["last_name"],
                           interest=output["primary_skills"],
                           location=output["location"],
                           color=COLOR)

if __name__ == '__main__':
    # Optional command line override
    parser = argparse.ArgumentParser()
    parser.add_argument('--color', required=False)
    args = parser.parse_args()

    if args.color:
        color_arg = args.color
        if color_arg in color_codes:
            COLOR = color_codes[color_arg]
            print(f"Using color from argument: {color_arg}")
        else:
            print(f"Invalid color '{color_arg}'. Supported: {SUPPORTED_COLORS}")
            exit(1)
    else:
        print(f"Using color from environment or default: {APP_COLOR}")

    app.run(host='0.0.0.0', port=8080, debug=True)
