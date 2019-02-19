from flask_wtf import FlaskForm
from wtforms import Form, StringField, SelectField, BooleanField, \
                    RadioField, FormField
from wtforms.validators import InputRequired, DataRequired

import subjects
from utils import MultiCheckboxField

class LoginForm(FlaskForm):
    pass

class LogoutForm(FlaskForm):
    pass


def make_electives_form():
    class ElectivesForm(Form):
        pass

    for block in subjects.electives_grouped:
        label, courses = subjects.electives_grouped[block]
        setattr(ElectivesForm, block, MultiCheckboxField(label, choices=courses))

    return ElectivesForm

class ScheduleSettingsForm(FlaskForm):
    create_calendar = RadioField('Исользвать', coerce=int, choices=[
            (1, 'Новый календарь'),
            (0, 'Существующий календарь'),
        ], default=1, validators=[InputRequired()])
    existing_calendar = SelectField('Существующий календарь')
    new_calendar = StringField('Новый календарь', default='МФТИ')

    use_alt_name = RadioField('Названия предметов',
            choices=[
                (1, 'По-русски'),
                (0, 'По документам'),
            ], default=1, coerce=int, validators=[InputRequired()])

    obligatory = BooleanField('Добавить обязательные предметы', default=True)
    electives = FormField(make_electives_form())

    def validate(self):
        success = super().validate()

        if self.create_calendar.data and not self.new_calendar.data:
            self.new_calendar.errors.append(
                    'Имя календаря должно быть непустым')
            success = False

        return success
