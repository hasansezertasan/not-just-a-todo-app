# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
from flask_admin import BaseView, expose


class AboutView(BaseView):
    @expose(url="/", methods=["GET"])
    def index(self):
        return self.render("admin/about.html")
