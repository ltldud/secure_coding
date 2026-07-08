from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db, limiter
from models import User, Product, Transaction
from forms import TransferForm

transfers_bp = Blueprint("transfers", __name__)


@transfers_bp.route("/transfer", methods=["GET", "POST"])
@login_required
@limiter.limit("30 per hour")
def transfer():
    form = TransferForm()
    if form.validate_on_submit():
        receiver = User.query.filter_by(username=form.receiver_username.data.strip()).first()
        amount = form.amount.data

        if receiver is None:
            flash("받는 사람을 찾을 수 없습니다.", "danger")
        elif receiver.id == current_user.id:
            flash("자기 자신에게는 송금할 수 없습니다.", "danger")
        elif receiver.status == "suspended":
            flash("정지된 사용자에게는 송금할 수 없습니다.", "danger")
        elif current_user.balance < amount:
            flash("잔액이 부족합니다.", "danger")
        else:
            _execute_transfer(current_user, receiver, amount, kind="transfer")
            flash(f"{receiver.username}님에게 {amount:,}원을 송금했습니다.", "success")
            return redirect(url_for("transfers.history"))

    return render_template("transfer.html", form=form, balance=current_user.balance)


@transfers_bp.route("/product/<product_id>/purchase", methods=["POST"])
@login_required
@limiter.limit("30 per hour")
def purchase(product_id):
    product = Product.query.get_or_404(product_id)

    if product.status != "active":
        flash("판매 중인 상품이 아닙니다.", "danger")
        return redirect(url_for("products.view_product", product_id=product_id))
    if product.seller_id == current_user.id:
        flash("자신의 상품은 구매할 수 없습니다.", "danger")
        return redirect(url_for("products.view_product", product_id=product_id))
    if current_user.balance < product.price:
        flash("잔액이 부족합니다.", "danger")
        return redirect(url_for("products.view_product", product_id=product_id))

    seller = product.seller
    _execute_transfer(current_user, seller, product.price, kind="purchase", product=product)
    product.status = "sold"
    db.session.commit()

    flash("구매가 완료되었습니다.", "success")
    return redirect(url_for("products.view_product", product_id=product_id))


def _execute_transfer(sender, receiver, amount, kind="transfer", product=None):
    # Balance check + mutation happen in the same request/transaction and
    # commit together, so a failure here rolls back cleanly. Note: SQLite's
    # dev server here is single-threaded, so this isn't exposed to real
    # concurrent double-spend races; a production deployment on a real RDBMS
    # would additionally want `SELECT ... FOR UPDATE` (or an equivalent
    # optimistic version check) around the balance read.
    sender.balance -= amount
    receiver.balance += amount
    db.session.add(
        Transaction(
            sender_id=sender.id,
            receiver_id=receiver.id,
            amount=amount,
            kind=kind,
            product_id=product.id if product else None,
        )
    )
    db.session.commit()


@transfers_bp.route("/transactions")
@login_required
def history():
    txs = (
        Transaction.query.filter(
            db.or_(Transaction.sender_id == current_user.id, Transaction.receiver_id == current_user.id)
        )
        .order_by(Transaction.created_at.desc())
        .all()
    )
    user_ids = {tx.sender_id for tx in txs} | {tx.receiver_id for tx in txs}
    usernames = {u.id: u.username for u in User.query.filter(User.id.in_(user_ids)).all()}
    return render_template("transactions.html", txs=txs, me=current_user, usernames=usernames)
