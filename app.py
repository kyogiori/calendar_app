from flask import Flask, render_template, redirect, url_for, request
import calendar
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'  # Для безпеки сесій
Bootstrap(app)

# Ініціалізація SQLAlchemy
db = SQLAlchemy(app)


# Модель події
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Event {self.title}>'


@app.route('/calendar')
def calendar_view():
    # Отримання параметрів року та місяця з URL (або поточний місяць за замовчуванням)
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)

    # Отримання подій для вибраного місяця
    events = Event.query.filter(
        db.extract('year', Event.event_date) == year,
        db.extract('month', Event.event_date) == month
    ).all()

    # Групування подій за днями
    events_by_day = {day: [] for day in range(1, 32)}
    for event in events:
        events_by_day[event.event_date.day].append(event)

    # Створення структури календаря
    cal = calendar.Calendar()
    month_days = cal.itermonthdays2(year, month)  # (день, день тижня)

    return render_template(
        'calendar.html',
        year=year,
        month=month,
        month_days=month_days,
        events_by_day=events_by_day,
        month_name= calendar.month_name[month]
    )

# Головна сторінка - показує список подій
@app.route('/')
def index():
    events = Event.query.order_by(Event.event_date).all()
    return render_template('index.html', events=events)


# Сторінка для додавання нової події
@app.route('/add', methods=['GET', 'POST'])
def add_event():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        event_date = datetime.strptime(request.form['event_date'], '%Y-%m-%dT%H:%M')

        new_event = Event(title=title, description=description, event_date=event_date)
        db.session.add(new_event)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_event.html')


# Сторінка для редагування події
@app.route('/edit/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)

    if request.method == 'POST':
        event.title = request.form['title']
        event.description = request.form['description']
        event.event_date = datetime.strptime(request.form['event_date'], '%Y-%m-%dT%H:%M')

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit_event.html', event=event)


# Сторінка для видалення події
@app.route('/delete/<int:event_id>')
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for('index'))


# Створення бази даних (потрібно викликати вручну при першому запуску)
def create_db():
    with app.app_context():
        db.create_all()


if __name__ == '__main__':
    create_db()
    app.run(debug=True, port= 5560)
