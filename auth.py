from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import check_password_hash
from flask_login import login_user
from data import User, db
from datetime import datetime, timedelta

auth = Blueprint("auth", __name__)
MAX_UNSUCCESSFUL_LOGINS = 5
BLOCK_TIME = timedelta(minutes=10)

@auth.route("/login")
def login():
    return render_template("login.html")


@auth.route("/login", methods=["POST"])
def login_post():
    password = request.form.get("password")

    user: User = User.query.filter_by(username="admin").first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if user.block_time and user.block_time > datetime.now():
        unblock_time = user.block_time - datetime.now()
        left_str = f"{unblock_time.seconds//60} minutes" if unblock_time.seconds//60 > 0 else f"{unblock_time.seconds} seconds"
        flash(f"You provided incorrect password too many times. Try again after {left_str}", "danger")
        return redirect(url_for("auth.login"))
    if not check_password_hash(user.password, password):
        user.unsuccesful_logins += 1
        if user.unsuccesful_logins >= MAX_UNSUCCESSFUL_LOGINS:
            user.block_time = datetime.now() + BLOCK_TIME
            user.unsuccesful_logins = 0
            flash(f"You provided incorrect password too many times and are blocked for {BLOCK_TIME.seconds//60} minutes", "danger")
        else:
            flash("Incorrect password. Try again", "danger")
        db.session.add(user)
        db.session.commit()
        


        return redirect(
            url_for("auth.login")
        )  # if the user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    user.unsuccesful_logins = 0
    user.block_time = None
    db.session.add(user)
    db.session.commit()
    login_user(user=user, remember=True)
    return redirect(url_for("main.index"))
