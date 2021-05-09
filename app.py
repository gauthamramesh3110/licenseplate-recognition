from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)


class Entries(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    licenseplate_number = db.Column(db.String(10), nullable=False)
    entry_time = db.Column(db.DateTime, default=datetime.utcnow)
    exit_time = db.Column(db.DateTime)
    payment_approved = db.Column(db.Boolean, default=False)

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


@app.route("/registeruser", methods=["POST"])
def register_user():

    existing_user = User.query.filter_by(username=request.json['username']).first()
    if existing_user != None:
        return {
            'status' : 'failure',
            'message' : 'Username already exists'
        }
    
    existing_licenseplate =  User.query.filter_by(licenseplate_number=request.json['licenseplate_number']).first()
    if existing_licenseplate != None:
        return {
            'status' : 'failure',
            'message' : 'Licenseplate already associated with a user.'
        }

    new_user = User(
        username=request.json["username"],
        email=request.json["email"],
        password=request.json["password"],
        licenseplate_number=request.json["licenseplate_number"],
    )
    print(new_user)

    try:
        db.session.add(new_user)
        db.session.commit()

        return {
            'status' : 'success',
            'message' : 'Added User'
        }
    
    except:
        return {
            'status' : 'failure',
            'message' : 'Unable to create User'
        }


if __name__ == "__main__":
    app.run(debug=True)
