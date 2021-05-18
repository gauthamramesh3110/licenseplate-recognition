from flask import Flask, request, render_template, url_for, redirect, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from sqlalchemy.orm import defaultload
from licenseplate_recognition import recognize
import cv2
import numpy as np

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)


class Entries(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    licenseplate_number = db.Column(db.String(10), nullable=False)
    entry_time = db.Column(db.DateTime, default=datetime.utcnow)
    exit_time = db.Column(db.DateTime)
    location = db.Column(db.String(30), nullable=False)
    payment_amount = db.Column(db.Integer, default=0)
    payment_approved = db.Column(db.Boolean, default=False)
    exited = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return "<Entry %r>" % self.licenseplate_number


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(30), nullable=False)
    licenseplate_number = db.Column(db.String(10), nullable=False)
    wallet_amount = db.Column(db.Integer, default=0)

    def __repr__(self):
        return "<User %r>" % self.username


@app.route("/auth")
def auth():
    return render_template("auth.html")


@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/addentry", methods=["POST"])
def add_entry():

    new_entry = Entries(licenseplate_number=request.json["licenseplate_number"], location=request.json["location"])

    try:
        db.session.add(new_entry)
        db.session.commit()

        return {"status": "success", "message": "Added new entry successfully"}
    except:
        return {"status": "failure", "message": "Error adding new entry"}


@app.route("/addexit", methods=["POST"])
def add_exit():

    existing_entry = Entries.query.filter_by(licenseplate_number=request.json["licenseplate_number"], exit_time=None).first()

    if existing_entry == None:
        return {"status": "failure", "message": "No open entry found"}

    existing_entry.exit_time = datetime.now()
    parking_time = existing_entry.exit_time - existing_entry.entry_time
    parking_time = parking_time.total_seconds() // 3600
    existing_entry.payment_amount = parking_time * int(request.json["amount_per_hour"])
    existing_entry.exited = True

    try:
        db.session.commit()
        return {"status": "success", "message": "Added Exit and Updated Amount"}
    except:
        return {"status": "failure", "message": "Unable to add exit"}


@app.route("/registeruser", methods=["POST"])
def register_user():
    existing_user = User.query.filter_by(username=request.form["username"]).first()
    if existing_user != None:
        return {"status": "failure", "message": "Username already exists"}

    existing_licenseplate = User.query.filter_by(licenseplate_number=request.form["licenseplate_number"]).first()
    if existing_licenseplate != None:
        return {"status": "failure", "message": "Licenseplate already associated with a user."}

    new_user = User(
        username=request.form["username"],
        email=request.form["email"],
        password=request.form["password"],
        licenseplate_number=request.form["licenseplate_number"],
    )
    print(new_user)

    try:
        db.session.add(new_user)
        db.session.commit()

        response = redirect("/home")
        response.set_cookie("username", new_user.username)
        response.set_cookie("password", new_user.password)
        response.set_cookie("loggedin", "true")

        return response

    except:
        return {"status": "failure", "message": "Unable to create User"}


@app.route("/loginuser", methods=["POST"])
def login_user():
    user = User.query.filter_by(username=request.form["username"]).first()

    if user == None:
        return {"status": "failure", "message": "Username is not available"}
    else:
        if user.password == request.form["password"]:
            response = make_response(redirect("/home"))
            response.set_cookie("username", user.username)
            response.set_cookie("password", user.password)
            response.set_cookie("loggedin", "true")

            return response
        else:
            return {"status": "failure", "message": "Incorrect password"}


@app.route("/addtowallet", methods=["POST"])
def add_to_wallet():
    user = User.query.filter_by(username=request.headers["username"], password=request.headers["password"]).first()
    if user == None:
        return {"status": "failure", "message": "invalid credentials"}
    else:
        print("hello")
        print(request.json["additional_wallet_amount"])
        user.wallet_amount += int(request.json["additional_wallet_amount"])

        try:
            db.session.commit()
            print("added")
            return {"status": "success", "message": "Updated wallet amount", "wallet_amount": user.wallet_amount}
        except:
            return {"status": "failure", "message": "Error updating wallet amount"}


@app.route("/getwalletamount", methods=["GET"])
def get_wallet_amount():
    user = User.query.filter_by(username=request.headers["username"], password=request.headers["password"]).first()
    if user == None:
        return {"status": "failure", "message": "invalid credentials"}

    return {"status": "success", "message": "Retrived wallet amount", "wallet_amount": user.wallet_amount}


@app.route("/getpendingapproval", methods=["GET"])
def get_pending_approval():

    user = User.query.filter_by(username=request.headers["username"], password=request.headers["password"]).first()
    if user == None:
        return {"status": "failure", "message": "invalid credentials"}

    pending_approval = Entries.query.filter_by(licenseplate_number=user.licenseplate_number, payment_approved=False, exited=True).first()
    if pending_approval == None:
        return {"status": "success", "message": "No approval item found."}

    return {
        "status": "success",
        "message": "Approval item found",
        "id": pending_approval.id,
        "location": pending_approval.location,
        "payment_amount": pending_approval.payment_amount,
    }


@app.route("/scan_image", methods=["POST"])
def scan_image():
    image_file = request.files["image_file"].read()
    npimg = np.fromstring(image_file, np.uint8)
    image = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    image = np.array(image)

    result = recognize([image])

    return {"licenseplate_number": result}


@app.route("/approve", methods=["POST"])
def approve():
    user = User.query.filter_by(username=request.headers["username"], password=request.headers["password"]).first()
    if user == None:
        return {"status": "failure", "message": "invalid credentials"}

    pending_approval = Entries.query.filter_by(id=request.json["id"]).first()
    user.wallet_amount -= pending_approval.payment_amount
    pending_approval.payment_approved = True

    try:
        db.session.commit()
        return {"status": "success", "message": "Approved Payment Successfully", "wallet_amount": user.wallet_amount}
    except:
        return {"status": "failure", "message": "Unable to Approve payment"}


if __name__ == "__main__":
    app.run(debug=True)
