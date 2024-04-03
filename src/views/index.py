# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
# Copyright (C) 2024 <hasansezertasan@gmail.com>
from flask_admin import AdminIndexView, expose


class IndexView(AdminIndexView):
    @expose(url="/", methods=["GET"])
    def index(self):
        return self.render("admin/index.html")

    def is_visible(self):
        return False
