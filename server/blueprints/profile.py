from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db, limiter
from models import User
from forms import ProfileForm, PasswordChangeForm

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile", methods=["GET", "POST"])
@login_required
def mypage():
    form = ProfileForm(obj=current_user)
    pw_form = PasswordChangeForm()
    return render_template("profile.html", form=form, pw_form=pw_form)


@profile_bp.route("/profile/bio", methods=["POST"])
@login_required
def update_bio():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.bio = form.bio.data
        db.session.commit()
        flash("프로필이 업데이트되었습니다.", "success")
    else:
        for errs in form.errors.values():
            for e in errs:
                flash(e, "danger")
    return redirect(url_for("profile.mypage"))


@profile_bp.route("/profile/password", methods=["POST"])
@login_required
@limiter.limit("10 per hour")
def update_password():
    pw_form = PasswordChangeForm()
    if pw_form.validate_on_submit():
        if not current_user.check_password(pw_form.current_password.data):
            flash("현재 비밀번호가 올바르지 않습니다.", "danger")
            return redirect(url_for("profile.mypage"))
        current_user.set_password(pw_form.new_password.data)
        db.session.commit()
        flash("비밀번호가 변경되었습니다.", "success")
    else:
        for errs in pw_form.errors.values():
            for e in errs:
                flash(e, "danger")
    return redirect(url_for("profile.mypage"))


@profile_bp.route("/user/<username>")
@login_required
def view_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template("public_profile.html", profile_user=user)
