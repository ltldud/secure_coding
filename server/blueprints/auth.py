from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db, limiter
from models import User
from forms import RegisterForm, LoginForm, ForgotUsernameForm, ForgotVerifyForm
from config import Config

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("products.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(username=form.username.data).first()
        if existing is not None:
            flash("이미 존재하는 사용자명입니다.", "danger")
            return render_template("register.html", form=form)

        user = User(username=form.username.data, balance=Config.STARTING_BALANCE)
        user.set_password(form.password.data)
        user.security_question = form.security_question.data.strip()
        user.set_security_answer(form.security_answer.data)
        db.session.add(user)
        db.session.commit()
        flash("회원가입이 완료되었습니다. 로그인 해주세요.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("15 per 5 minutes")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("products.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        # Same generic error whether the username doesn't exist or the
        # password is wrong / account locked, so login can't be used to
        # enumerate valid usernames.
        generic_error = "아이디 또는 비밀번호가 올바르지 않습니다."

        if user is None:
            flash(generic_error, "danger")
            return render_template("login.html", form=form)

        if user.is_locked():
            flash("계정이 잠겨 있습니다. 잠시 후 다시 시도하세요.", "danger")
            return render_template("login.html", form=form)

        if user.status == "suspended":
            flash("휴면(정지) 처리된 계정입니다. 관리자에게 문의하세요.", "danger")
            return render_template("login.html", form=form)

        if not user.check_password(form.password.data):
            user.register_failed_login(Config.LOGIN_FAIL_LIMIT, Config.LOGIN_LOCK_MINUTES)
            db.session.commit()
            flash(generic_error, "danger")
            return render_template("login.html", form=form)

        user.reset_failed_login()
        db.session.commit()
        session.permanent = True
        login_user(user)
        flash("로그인 성공!", "success")
        return redirect(url_for("products.dashboard"))

    return render_template("login.html", form=form)


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("products.dashboard"))

    form = ForgotUsernameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.has_security_question():
            session["pwreset_user_id"] = user.id
            return redirect(url_for("auth.forgot_password_verify"))
        # Same generic message whether the account doesn't exist or simply
        # never set a security question, so this can't be used to probe
        # which usernames exist.
        flash("아이디 또는 비밀번호 찾기 질문 설정을 확인할 수 없습니다.", "danger")

    return render_template("forgot_password.html", form=form)


@auth_bp.route("/forgot-password/verify", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def forgot_password_verify():
    user_id = session.get("pwreset_user_id")
    user = db.session.get(User, user_id) if user_id else None
    if user is None or not user.has_security_question():
        session.pop("pwreset_user_id", None)
        return redirect(url_for("auth.forgot_password"))

    form = ForgotVerifyForm()
    if form.validate_on_submit():
        if not user.check_security_answer(form.security_answer.data):
            flash("답변이 올바르지 않습니다.", "danger")
            return render_template("forgot_password_verify.html", form=form, question=user.security_question)

        user.set_password(form.new_password.data)
        user.reset_failed_login()
        db.session.commit()
        session.pop("pwreset_user_id", None)
        flash("비밀번호가 재설정되었습니다. 새 비밀번호로 로그인해주세요.", "success")
        return redirect(url_for("auth.login"))

    return render_template("forgot_password_verify.html", form=form, question=user.security_question)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("로그아웃되었습니다.", "info")
    return redirect(url_for("index"))
