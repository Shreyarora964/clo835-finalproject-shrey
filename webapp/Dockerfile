# FROM python:3.8-slim
# WORKDIR /app
# COPY . /app
# COPY templates/ /app/templates/
# RUN pip install -r requirements.txt
# ENV FLASK_APP=app.py
# CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]


# Simple Flask image
FROM python:3.11-slim

WORKDIR /app

# Install deps
COPY webapp/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY webapp/ /app/

# Flask runs on port 81 for the assignment
ENV FLASK_APP=app.py
EXPOSE 81

# Start the server (simple for school project)
CMD ["flask", "run", "--host=0.0.0.0", "--port=81"]
