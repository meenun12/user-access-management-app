from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SelectMultipleField, SelectField, BooleanField
from wtforms.validators import InputRequired, Length, Email
from sqlalchemy.exc import IntegrityError
from flask import jsonify
from wtforms.widgets import CheckboxInput, ListWidget

app = Flask(__name__)
app.config["SECRET_KEY"] = "user-access-management"  # Replace with your own secret key
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///user_access_management.db"
db = SQLAlchemy(app)

# Define the association table
team_employee = db.Table('team_employee',
                         db.Column('team_id', db.Integer, db.ForeignKey('team.id'), primary_key=True),
                         db.Column('emp_id', db.Integer, db.ForeignKey('employee.id'), primary_key=True)
                         )


# Define the team model
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    employees = db.relationship('Employee', secondary=team_employee, lazy='subquery',
                               backref=db.backref('teams', lazy=True))


# Define the Employee model
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)


class TeamForm(FlaskForm):
    """
    A Flask-WTF form that allows users to enter a team name.
`   """

    name = StringField(
        "Name",
        validators=[
            InputRequired("Input required!"),
            Length(
                min=2, max=50, message="team name is not the required length."
            ),
        ],
    )


class EmployeeForm(FlaskForm):
    """
    A Flask-WTF form that allows users to add employees
`   """

    name = StringField(
        "Name",
        validators=[
            InputRequired("Input required!"),
            Length(
                min=2, max=10, message="Employee name is not the required length."
            ),
        ],
    )
    email = StringField("Email",
                        [InputRequired("Please enter your email address."), Email()])


class AssignTeamForm(FlaskForm):

    """
    This form enables Product Owners to grant access permissions to employees,
    allowing them to view their respective dashboards.
`   """

    email = StringField("Email",
                        [InputRequired("Please enter your email address."), Email()])
    def __init__(self, *args, **kwargs):
        super(AssignTeamForm, self).__init__(*args, **kwargs)
        self.teams.choices = [(team.id, team.name) for team in Team.query.all()]

    teams = SelectMultipleField('Teams', coerce=int, id='teams-field')


class CustomListWidget(ListWidget):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('class_', 'form-check')
        return super().__call__(field, **kwargs)


class CustomCheckboxInput(CheckboxInput):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('class_', 'form-check-input')
        return super().__call__(field, **kwargs)


class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class DashboardForm(FlaskForm):
    """
    This forms allows to see product owner how many users can access ING organization team(s)
`   """
    team = SelectField('Teams', coerce=int, id='teams-field')
    employees = MultiCheckboxField('Employees', id='emps-field', widget=CustomListWidget(prefix_label=False),
                                   option_widget=CustomCheckboxInput())

    def __init__(self, *args, **kwargs):

        super(DashboardForm, self).__init__(*args, **kwargs)

        # Populate the team selector with choices from the database
        self.team.choices = [(team.id, team.name) for team in Team.query.order_by(Team.id.desc()).all()]

        # Set the default value for the team selector to the first team added to the database
        default_team = Team.query.order_by(Team.id.asc()).first()
        self.team.data = default_team.id

        # If a default team exists, populate the employee checkboxes with employees assigned to that team
        if default_team:
            employees = db.session.query(Employee.id, Employee.email).join(Team.employees).filter(Team.id == default_team.id)
            self.employees.choices = [(str(emp[0]), emp[1]) for emp in employees.all()]
            selected_employees = [str(emp[0]) for emp in employees.all()]
            self.employees.data = selected_employees

@app.route("/", methods=["GET", "POST"])
def dashboard():

    """
    This is dashboard, where product owner can see which employees are assign to a team
    """

    form = DashboardForm()
    return render_template('dashboard.html', form=form, selected_team = form.team.data)

@app.route("/add_team", methods=["GET", "POST"])
def add_team():
    """
    A Flask route function that allows users to add a new team.
`   """

    form = TeamForm()

    if form.validate_on_submit():

        try:
            # Create a new Team object with the name from the form data
            team_name = Team(name=form.name.data)
            db.session.add(team_name)
            db.session.commit()
            flash("Team has been added successfully!", "success")
        except IntegrityError:
            db.session.rollback()
            flash("Team already exists!", "error")

    return render_template("add_team.html", form=form)


@app.route("/add_employee", methods=["GET", "POST"])
def add_employee():

    """
    A Flask route function that allows users to add an employee
`   """

    form = EmployeeForm()

    if form.validate_on_submit():

        try:
            # Create a new Employee object with the name and email from the form data
            emp = Employee(name=form.name.data, email=form.email.data)
            db.session.add(emp)
            db.session.commit()
            flash("Employee has been added successfully!", "success")
        except IntegrityError:
            db.session.rollback()
            flash("Employee already exists!", "error")

    return render_template("add_Employee.html", form=form)

@app.route("/assign_team", methods=["GET", "POST"])
def assign_team():
    """
    Flask route to handle POST requests for assigning a team to an employee
    """
    form = AssignTeamForm()
    if form.validate_on_submit():
        email = form.email.data
        teams = form.teams.data

        # Get the employee with the specified email from the database
        employee = Employee.query.filter_by(email=email).first()

        # Remove the employee from all teams they're currently assigned to
        db.session.execute(team_employee.delete().where(team_employee.c.emp_id == employee.id))
        db.session.commit()

        # Add the employee to the teams specified in the request
        for team_id in teams:
            # Create a new record in the team_employee table linking the employee to the team
            stmt = team_employee.insert().values(team_id=team_id, emp_id=employee.id)
            db.session.execute(stmt)
            db.session.commit()

        flash('Team(s) assigned successfully!', 'success')
        return redirect(url_for('assign_team'))
    return render_template('assign_team.html', form=form)


@app.route('/autocomplete', methods=['POST'])
def autocomplete():

    search_term = request.form['search_term']

    # Query the database for employees whose email matches the search term
    results = Employee.query.filter(Employee.email.like(f'%{search_term}%')).all()

    return jsonify([{'id': result.id, 'email': result.email} for result in results])

# Route to handle AJAX request for department associated with email
@app.route('/get_existing_team_ids', methods=['POST'])
def get_existing_team_ids():

    emp_id = request.form['emp_id']

    # Query the team_employee table for team_id values where emp_id matches
    query = db.session.query(team_employee.c.team_id).filter(team_employee.c.emp_id == emp_id)

    # Get the results of the query as a list of team_id values
    team_ids = [result[0] for result in query.all()]

    return jsonify(team_ids=team_ids)

@app.route('/get_assigned_employees', methods=['POST'])
def get_assigned_employees():

    team_id = request.form['team_id']

    # Query the team_employee, employee table and fetches employees
    employees = db.session.query(Employee.id, Employee.email)\
        .join(team_employee, Employee.id == team_employee.c.emp_id)\
        .filter(team_employee.c.team_id == team_id)\
        .all()

    # Get the results of the query as a list of dictionary of employees values
    employees = [{'id': employee.id, 'email': employee.email} for employee in employees]

    return jsonify(employees)

if __name__ == '__main__':
    """
    Create the database tables based on the defined models within the Flask app context.
`   """
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5004)


