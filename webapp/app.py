from flask import Flask, render_template, request
from pymysql import connections
import os
import argparse
import boto3
import logging

app = Flask(__name__)

# -------------------------
# Environment variables
# -------------------------
# DB (from K8s Secret + ConfigMap)
DBHOST = os.environ.get("DBHOST", "localhost")
DBUSER = os.environ.get("DBUSER", "root")
DBPWD = os.environ.get("DBPWD", "password")
DATABASE = os.environ.get("DATABASE", "employees")
DBPORT = int(os.environ.get("DBPORT", 3306))

# Background & group header (from K8s ConfigMap)
S3_BUCKET = os.environ.get("S3_BUCKET", "")
BG_IMAGE = os.environ.get("BG_IMAGE", "")              # e.g. "bg1.jpg"
GROUP_NAME = os.environ.get("GROUP_NAME", "Team Shrey")
GROUP_SLOGAN = os.environ.get("GROUP_SLOGAN", "We ship demos!")

# AWS creds (from K8s Secret)
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_SESSION_TOKEN = os.environ.get("AWS_SESSION_TOKEN", "")  # optional

# -------------------------
# Logging
# -------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webapp")

# -------------------------
# Background image handling
# -------------------------
STATIC_DIR = os.path.join(app.root_path, "static")
LOCAL_BG_PATH = os.path.join(STATIC_DIR, "background.jpg")

def download_bg_image_if_needed():
    """
    Download the private S3 background image to static/background.jpg.
    Logs the exact s3:// URL.
    Keeps it simple: download if the local file is missing.
    """
    if not S3_BUCKET or not BG_IMAGE:
        logger.warning("S3_BUCKET or BG_IMAGE is not set. Skipping background download.")
        return

    # Ensure static dir exists
    os.makedirs(STATIC_DIR, exist_ok=True)

    if os.path.exists(LOCAL_BG_PATH):
        # Already downloaded for this pod lifecycle; keep it simple.
        return

    logger.info(f"Downloading background image from s3://{S3_BUCKET}/{BG_IMAGE}")

    # Basic boto3 session using provided creds (works with K8s Secret)
    session = boto3.session.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY or None,
        aws_session_token=AWS_SESSION_TOKEN or None,
        region_name=AWS_REGION
    )
    s3 = session.client("s3")

    try:
        s3.download_file(S3_BUCKET, BG_IMAGE, LOCAL_BG_PATH)
        logger.info(f"Downloaded to {LOCAL_BG_PATH}")
    except Exception as e:
        logger.exception(f"Failed to download s3://{S3_BUCKET}/{BG_IMAGE}: {e}")

# -------------------------
# Optional color support kept for compatibility
# -------------------------
APP_COLOR = os.environ.get("APP_COLOR", "lime")
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

# -------------------------
# DB connection
# -------------------------
try:
    db_conn = connections.Connection(
        host=DBHOST, port=DBPORT, user=DBUSER, password=DBPWD, db=DATABASE
    )
except Exception as e:
    print("ERROR: Could not connect to MySQL database.")
    print(e)
    # Do not exit(1) in k8s; app can still load the UI and you can fix DB separately
    db_conn = None

# -------------------------
# Routes
# -------------------------
@app.route("/", methods=['GET', 'POST'])
def home():
    download_bg_image_if_needed()
    return render_template(
        'addemp.html',
        color=COLOR,
        group_name=GROUP_NAME,
        group_slogan=GROUP_SLOGAN,
        bg_url="/static/background.jpg"
    )

@app.route("/about", methods=['GET'])
def about():
    download_bg_image_if_needed()
    return render_template(
        'about.html',
        color=COLOR,
        group_name=GROUP_NAME,
        group_slogan=GROUP_SLOGAN,
        bg_url="/static/background.jpg"
    )

@app.route("/addemp", methods=['POST'])
def AddEmp():
    download_bg_image_if_needed()
    if not db_conn:
        return "Database connection not available.", 500

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

    return render_template(
        'addempoutput.html',
        name=emp_name,
        color=COLOR,
        group_name=GROUP_NAME,
        group_slogan=GROUP_SLOGAN,
        bg_url="/static/background.jpg"
    )

@app.route("/getemp", methods=['GET'])
def GetEmp():
    download_bg_image_if_needed()
    return render_template(
        "getemp.html",
        color=COLOR,
        group_name=GROUP_NAME,
        group_slogan=GROUP_SLOGAN,
        bg_url="/static/background.jpg"
    )

@app.route("/fetchdata", methods=['POST'])
def FetchData():
    download_bg_image_if_needed()
    if not db_conn:
        return "Database connection not available.", 500

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

    return render_template(
        "getempoutput.html",
        id=output["emp_id"],
        fname=output["first_name"],
        lname=output["last_name"],
        interest=output["primary_skills"],
        location=output["location"],
        color=COLOR,
        group_name=GROUP_NAME,
        group_slogan=GROUP_SLOGAN,
        bg_url="/static/background.jpg"
    )

@app.route("/health")
def health():
    return "OK", 200

# -------------------------
# Main
# -------------------------
if __name__ == '__main__':
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

    # Listen on port 81 for the assignment requirement (no debug in prod)
    app.run(host='0.0.0.0', port=81)
