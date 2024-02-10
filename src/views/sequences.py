import datetime

from flask import redirect, url_for
from flask_admin import expose
from flask_admin.model.template import EndpointLinkRowAction, LinkRowAction, TemplateLinkRowAction
from flask_login import current_user
from markupsafe import Markup
from wtforms import TextAreaField

from src.db import Sequence, SequenceTemplate, Task, TaskTemplate, db

from .mixins import MemberMixin, MemberPropertyMixin, ModelViewMixin


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
    form_overrides = dict(
        description=TextAreaField,
    )
    inline_models = [
        (
            TaskTemplate,
            dict(
                form_columns=[
                    TaskTemplate.id,
                    TaskTemplate.name,
                    TaskTemplate.description,
                ],
            ),
        )
    ]
    column_formatters = {
        "task_count": lambda v, c, m, p: len(m.tasks),
        "tasks": lambda v, c, m, p: Markup("<br>".join([task.name for task in m.tasks])),
    }
    column_extra_row_actions = [
        EndpointLinkRowAction(
            "fa fa-copy",
            "sequence-template.populate",
            title="Populate",
            id_arg="id",
        )
    ]

    def on_model_change(self, form, model: SequenceTemplate, is_created: bool):
        if is_created:
            model.user_id = current_user.id
            for idx, _ in enumerate(model.tasks):
                model.tasks[idx].user_id = current_user.id
        super().on_model_change(form, model, is_created)

    @expose("/populate/<int:id>", methods=["GET"])
    def populate(self, id):
        sequence_template = SequenceTemplate.find_by_id(id)
        sequence = Sequence(
            name=sequence_template.name,
            description=sequence_template.description,
            template_id=id,
            user_id=current_user.id,
        )
        for task_template in sequence_template.tasks:
            task = Task(name=task_template.name, description=task_template.description, user_id=current_user.id)
            sequence.tasks.append(task)
        sequence.upsert()
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
    column_formatters = {
        "tasks_summary": lambda v, c, m, p: Markup("<br>".join(m.tasks_summary)),
        "progress": lambda v, c, m, p: f"{m.completed_task_count}/{m.task_count}",
    }

    @expose("/progress/<int:id>", methods=["GET"])
    def progress(self, id):
        sequence = Sequence.find_by_id(id)
        return self.render("admin/sequence-progress.html", sequence=sequence)

    @expose("/progress/<int:_id>/task/<int:task_id>/complete", methods=["GET"])
    def complete(self, _id, task_id):
        utcnow = datetime.datetime.utcnow()
        task = Task.query.filter(Task.id == task_id).first()
        task.date_completed = utcnow
        task.upsert()
        return redirect(url_for("sequence.progress", id=_id))
