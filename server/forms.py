from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange, ValidationError

from security import is_valid_username, is_valid_password


class UsernameField(StringField):
    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)
        if self.data:
            self.data = self.data.strip()


def validate_username(form, field):
    if not is_valid_username(field.data):
        raise ValidationError("아이디는 영문/숫자/밑줄 3~20자만 가능합니다.")


def validate_password_strength(form, field):
    if not is_valid_password(field.data):
        raise ValidationError("비밀번호는 8~64자, 영문과 숫자를 각 1자 이상 포함해야 합니다.")


class RegisterForm(FlaskForm):
    username = UsernameField("아이디", validators=[DataRequired(), validate_username])
    password = PasswordField("비밀번호", validators=[DataRequired(), validate_password_strength])
    confirm = PasswordField(
        "비밀번호 확인",
        validators=[DataRequired(), EqualTo("password", message="비밀번호가 일치하지 않습니다.")],
    )


class LoginForm(FlaskForm):
    username = UsernameField("아이디", validators=[DataRequired(), Length(max=30)])
    password = PasswordField("비밀번호", validators=[DataRequired(), Length(max=64)])


class ProfileForm(FlaskForm):
    bio = TextAreaField("소개글", validators=[Length(max=500)])


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField("현재 비밀번호", validators=[DataRequired()])
    new_password = PasswordField("새 비밀번호", validators=[DataRequired(), validate_password_strength])
    confirm = PasswordField(
        "새 비밀번호 확인",
        validators=[DataRequired(), EqualTo("new_password", message="비밀번호가 일치하지 않습니다.")],
    )


class ProductForm(FlaskForm):
    title = StringField("상품명", validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField("상품 설명", validators=[DataRequired(), Length(min=1, max=2000)])
    price = IntegerField("가격", validators=[DataRequired(), NumberRange(min=0, max=1_000_000_000)])


class ReportForm(FlaskForm):
    target_type = HiddenField("target_type", validators=[DataRequired()])
    target_id = HiddenField("target_id", validators=[DataRequired()])
    reason = TextAreaField("신고 사유", validators=[DataRequired(), Length(min=5, max=500)])

    def validate_target_type(self, field):
        if field.data not in ("user", "product"):
            raise ValidationError("잘못된 신고 대상입니다.")


class TransferForm(FlaskForm):
    receiver_username = StringField("받는 사람 아이디", validators=[DataRequired(), Length(max=30)])
    amount = IntegerField("금액", validators=[DataRequired(), NumberRange(min=1, max=1_000_000_000)])


class SearchForm(FlaskForm):
    class Meta:
        csrf = False

    q = StringField("검색어", validators=[Length(max=100)])
