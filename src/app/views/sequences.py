# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
from flask import redirect, url_for
from flask_admin import expose
from flask_admin.model.template import EndpointLinkRowAction
from flask_login import current_user
from markupsafe import Markup, escape
from wtforms import TextAreaField

from app.db.models import Sequence, SequenceTemplate, TaskTemplate
from app.services import sequences as sequence_service
from app.views.mixins import MemberMixin, MemberPropertyMixin, ModelViewMixin


class SequenceTemplateView(MemberMixin, MemberPropertyMixin, ModelViewMixin):
    column_list = [
        SequenceTemplate.name,
        SequenceTemplate.description,
        "task_count",
    ]
    column_details_list = [
        SequenceTemplate.date_created,
        SequenceTemplate.date_updated,
        SequenceTemplate.name,
        SequenceTemplate.description,
        "tasks",
        "task_count",
    ]
    column_labels = {
        SequenceTemplate.date_created: "Date Created",
        SequenceTemplate.date_updated: "Date Updated",
        SequenceTemplate.name: "Name",
        SequenceTemplate.description: "Description",
    }
    form_columns = [
        SequenceTemplate.name,
        SequenceTemplate.description,
    ]
    form_overrides = {
        "description": TextAreaField,
    }
    inline_models = [
        (
            TaskTemplate,
            {
                "form_columns": [
                    TaskTemplate.id,
                    TaskTemplate.name,
                    TaskTemplate.description,
                ],
            },
        ),
    ]
    # `escape()` each task name before joining — task.name is user-supplied
    # and would otherwise be rendered as raw HTML (XSS). The literal `<br>`
    # separator is the only HTML we intend to emit.
    column_formatters = {
        "task_count": lambda _v, _c, m, _p: len(m.tasks),
        "tasks": lambda _v, _c, m, _p: Markup("<br>").join(
            escape(task.name) for task in m.tasks
        ),
    }
    column_extra_row_actions = [
        EndpointLinkRowAction(
            "fa fa-copy",
            "sequence-template.populate",
            title="Populate",
            id_arg="id",
        ),
    ]

    def on_model_change(self, form, model: SequenceTemplate, is_created: bool) -> None:
        if is_created:
            model.user_id = current_user.id
            for idx, _ in enumerate(model.tasks):
                model.tasks[idx].user_id = current_user.id
        super().on_model_change(form, model, is_created)

    @expose("/populate/<int:id>", methods=["GET"])
    def populate(self, id):
        sequence = sequence_service.instantiate_from_template(
            template_id=id, user_id=current_user.id
        )
        return redirect(url_for("sequence.progress", id=sequence.id))


class SequenceView(MemberMixin, MemberPropertyMixin, ModelViewMixin):
    can_create = False
    can_edit = False

    column_list = [
        Sequence.date_created,
        Sequence.name,
        Sequence.description,
        "progress",
    ]
    column_details_list = [
        Sequence.date_created,
        Sequence.date_updated,
        Sequence.name,
        Sequence.description,
        "tasks_summary",
        "progress",
    ]
    column_labels = {
        Sequence.date_created: "Date Created",
        Sequence.date_updated: "Date Updated",
        Sequence.name: "Name",
        Sequence.description: "Description",
        "tasks_summary": "Tasks",
        "progress": "Progress",
    }
    column_extra_row_actions = [
        EndpointLinkRowAction(
            "fa fa-play",
            endpoint="sequence.progress",
            title="Progress",
            id_arg="id",
        ),
    ]
    # See `SequenceTemplateView.column_formatters` — the same XSS escape
    # rule applies: task names embedded in `tasks_summary` are user data.
    column_formatters = {
        "tasks_summary": lambda _v, _c, m, _p: Markup("<br>").join(
            escape(s) for s in m.tasks_summary
        ),
        "progress": lambda _v, _c, m, _p: f"{m.completed_task_count}/{m.task_count}",
    }

    @expose("/progress/<int:id>", methods=["GET"])
    def progress(self, id):
        sequence = sequence_service.get_sequence(id)
        return self.render("admin/sequence-progress.html", sequence=sequence)

    @expose("/progress/<int:_id>/task/<int:task_id>/complete", methods=["GET"])
    def complete(self, _id: int, task_id: int):
        sequence_service.mark_task_completed(task_id=task_id)
        return redirect(url_for("sequence.progress", id=_id))
