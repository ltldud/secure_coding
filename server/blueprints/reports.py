from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from extensions import db, limiter
from models import Report, Product, User, AuditLog
from forms import ReportForm
from config import Config

reports_bp = Blueprint("reports", __name__)


def _resolve_target(target_type, target_id):
    if target_type == "product":
        return db.session.get(Product, target_id)
    if target_type == "user":
        return db.session.get(User, target_id)
    return None


@reports_bp.route("/report", methods=["GET", "POST"])
@login_required
@limiter.limit("20 per hour")
def report():
    target_type = request.values.get("target_type", "")
    target_id = request.values.get("target_id", "")

    form = ReportForm(target_type=target_type, target_id=target_id)

    if form.validate_on_submit():
        t_type = form.target_type.data
        t_id = form.target_id.data

        target = _resolve_target(t_type, t_id)
        if target is None:
            abort(404)

        if t_type == "user" and t_id == current_user.id:
            flash("자기 자신은 신고할 수 없습니다.", "danger")
            return redirect(url_for("products.dashboard"))
        if t_type == "product" and target.seller_id == current_user.id:
            flash("자신의 상품은 신고할 수 없습니다.", "danger")
            return redirect(url_for("products.dashboard"))

        rpt = Report(
            reporter_id=current_user.id,
            target_type=t_type,
            target_id=t_id,
            reason=form.reason.data.strip(),
        )
        db.session.add(rpt)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("이미 신고한 대상입니다.", "warning")
            return redirect(url_for("products.dashboard"))

        _apply_threshold(t_type, t_id)

        flash("신고가 접수되었습니다.", "success")
        return redirect(url_for("products.dashboard"))

    return render_template("report.html", form=form, target_type=target_type, target_id=target_id)


def _apply_threshold(target_type, target_id):
    # Reports an admin has dismissed as invalid must not keep counting toward
    # the auto-block/suspend threshold, or a dismissal would be undone by the
    # very next unrelated report against the same target.
    count = (
        Report.query.filter_by(target_type=target_type, target_id=target_id)
        .filter(Report.status != "dismissed")
        .count()
    )

    if target_type == "product":
        product = db.session.get(Product, target_id)
        if product is None or product.status == "blocked":
            return
        product.report_count = count
        if count >= Config.REPORT_THRESHOLD_PRODUCT:
            product.status = "blocked"
            Report.query.filter_by(target_type="product", target_id=target_id).update({"status": "actioned"})
            db.session.add(AuditLog(actor_id=None, action="auto_block_product", target=target_id))
        db.session.commit()

    elif target_type == "user":
        user = db.session.get(User, target_id)
        if user is None or user.status == "suspended":
            return
        user.report_count = count
        if count >= Config.REPORT_THRESHOLD_USER:
            user.status = "suspended"
            Report.query.filter_by(target_type="user", target_id=target_id).update({"status": "actioned"})
            db.session.add(AuditLog(actor_id=None, action="auto_suspend_user", target=target_id))
        db.session.commit()
