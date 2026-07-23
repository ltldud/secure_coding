from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from extensions import db
from models import User, Product, Report, Transaction, AuditLog

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def _log(action, target):
    db.session.add(AuditLog(actor_id=current_user.id, action=action, target=target))


@admin_bp.route("/")
@admin_required
def dashboard():
    stats = {
        "user_count": User.query.count(),
        "product_count": Product.query.count(),
        "pending_reports": Report.query.filter_by(status="pending").count(),
        "suspended_users": User.query.filter_by(status="suspended").count(),
        "blocked_products": Product.query.filter_by(status="blocked").count(),
    }
    recent_reports = Report.query.order_by(Report.created_at.desc()).limit(10).all()
    return render_template("admin/dashboard.html", stats=stats, recent_reports=recent_reports)


@admin_bp.route("/users")
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/<user_id>/suspend", methods=["POST"])
@admin_required
def suspend_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("자기 자신은 정지할 수 없습니다.", "danger")
        return redirect(url_for("admin.users"))
    user.status = "suspended"
    _log("admin_suspend_user", user.id)
    db.session.commit()
    flash(f"{user.username} 계정을 정지했습니다.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<user_id>/unsuspend", methods=["POST"])
@admin_required
def unsuspend_user(user_id):
    user = User.query.get_or_404(user_id)
    user.status = "active"
    user.report_count = 0
    _log("admin_unsuspend_user", user.id)
    db.session.commit()
    flash(f"{user.username} 계정 정지를 해제했습니다.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/products")
@admin_required
def products():
    all_products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("admin/products.html", products=all_products)


@admin_bp.route("/products/<product_id>/block", methods=["POST"])
@admin_required
def block_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.status = "blocked"
    _log("admin_block_product", product.id)
    db.session.commit()
    flash("상품을 차단했습니다.", "info")
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/<product_id>/unblock", methods=["POST"])
@admin_required
def unblock_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.status = "active"
    product.report_count = 0
    _log("admin_unblock_product", product.id)
    db.session.commit()
    flash("상품 차단을 해제했습니다.", "success")
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/<product_id>/delete", methods=["POST"])
@admin_required
def delete_product(product_id):
    from blueprints.products import _delete_product_image

    product = Product.query.get_or_404(product_id)
    _delete_product_image(product.image_filename)
    _log("admin_delete_product", product.id)
    db.session.delete(product)
    db.session.commit()
    flash("상품을 삭제했습니다.", "info")
    return redirect(url_for("admin.products"))


@admin_bp.route("/reports")
@admin_required
def reports():
    all_reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template("admin/reports.html", reports=all_reports)


@admin_bp.route("/reports/<report_id>/dismiss", methods=["POST"])
@admin_required
def dismiss_report(report_id):
    report = Report.query.get_or_404(report_id)
    report.status = "dismissed"
    _log("admin_dismiss_report", report.id)
    db.session.commit()
    flash("신고를 기각했습니다.", "info")
    return redirect(url_for("admin.reports"))


@admin_bp.route("/transactions")
@admin_required
def transactions():
    all_tx = Transaction.query.order_by(Transaction.created_at.desc()).limit(200).all()
    user_ids = {tx.sender_id for tx in all_tx} | {tx.receiver_id for tx in all_tx}
    usernames = {u.id: u.username for u in User.query.filter(User.id.in_(user_ids)).all()}
    return render_template("admin/transactions.html", txs=all_tx, usernames=usernames)
