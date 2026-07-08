from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from extensions import db
from models import Product
from forms import ProductForm, SearchForm

products_bp = Blueprint("products", __name__)

PAGE_SIZE = 12


@products_bp.route("/dashboard")
@login_required
def dashboard():
    search_form = SearchForm(request.args, meta={"csrf": False})
    query = Product.query.filter(Product.status != "blocked")

    q = (request.args.get("q") or "").strip()[:100]
    if q:
        escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = "%" + escaped + "%"
        query = query.filter(
            db.or_(
                Product.title.ilike(like, escape="\\"),
                Product.description.ilike(like, escape="\\"),
            )
        )

    page = max(request.args.get("page", 1, type=int), 1)
    pagination = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=PAGE_SIZE, error_out=False
    )

    return render_template(
        "dashboard.html",
        products=pagination.items,
        pagination=pagination,
        q=q,
        search_form=search_form,
    )


@products_bp.route("/product/new", methods=["GET", "POST"])
@login_required
def new_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            price=form.price.data,
            seller_id=current_user.id,
        )
        db.session.add(product)
        db.session.commit()
        flash("상품이 등록되었습니다.", "success")
        return redirect(url_for("products.view_product", product_id=product.id))
    return render_template("new_product.html", form=form)


@products_bp.route("/product/<product_id>")
@login_required
def view_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.status == "blocked" and product.seller_id != current_user.id and not current_user.is_admin():
        abort(404)
    return render_template("view_product.html", product=product, seller=product.seller)


@products_bp.route("/product/<product_id>/edit", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.seller_id != current_user.id:
        abort(403)

    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.title = form.title.data.strip()
        product.description = form.description.data.strip()
        product.price = form.price.data
        db.session.commit()
        flash("상품 정보가 수정되었습니다.", "success")
        return redirect(url_for("products.view_product", product_id=product.id))
    return render_template("edit_product.html", form=form, product=product)


@products_bp.route("/product/<product_id>/delete", methods=["POST"])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.seller_id != current_user.id and not current_user.is_admin():
        abort(403)
    db.session.delete(product)
    db.session.commit()
    flash("상품이 삭제되었습니다.", "info")
    return redirect(url_for("products.my_products"))


@products_bp.route("/my-products")
@login_required
def my_products():
    products = (
        Product.query.filter_by(seller_id=current_user.id)
        .order_by(Product.created_at.desc())
        .all()
    )
    return render_template("my_products.html", products=products)
