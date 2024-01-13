from flask_admin import AdminIndexView, expose

from .mixins import MemberMixin


class IndexView(MemberMixin, AdminIndexView):
    @expose(url="/", methods=["GET"])
    def index(self):
        return self.render("admin/index.html")

    def is_visible(self):
        return False
