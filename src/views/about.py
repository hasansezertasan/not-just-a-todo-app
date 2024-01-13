from flask_admin import BaseView, expose

from .mixins import MemberMixin


class AboutView(BaseView):
    @expose(url="/", methods=["GET"])
    def index(self):
        return self.render("admin/about.html")
