from flask import redirect, url_for
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

from src._types import UserRole


class MemberMixin:
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("login.index"))


class MemberPropertyMixin(ModelView):
    def get_query(self):
        return super().get_query().filter_by(user_id=current_user.id)

    def get_count_query(self):
        return super().get_count_query().filter_by(user_id=current_user.id)


class AnonymousMixin:
    def is_accessible(self):
        return not current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("admin.index"))


class ModelViewMixin(ModelView):
    named_filter_urls = True
    column_display_pk = True
    column_display_actions = True
    column_display_row_actions = True
    column_display_all_relations = True
    column_auto_select_related = True
    can_view_details = True
    can_edit = True
    can_create = True
    can_delete = True
    can_set_page_size = True
    page_size = 50
