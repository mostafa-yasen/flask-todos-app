import sys
from flask import Flask, json, render_template, request, redirect, url_for, jsonify, abort
from flask.globals import session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import backref

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://postgres:password@localhost:5432/todos_app"
db = SQLAlchemy(app, session_options={"expire_on_commit": False})

migrate = Migrate(app, db)


class TodoList(db.Model):
  __tablename__ = "todo_lists"
  id = db.Column(db.Integer, primary_key=1)
  name = db.Column(db.String, nullable=0)

  todos = db.relationship('ToDo', backref="list", lazy=True)

  def __repr__(self):
      return f"<TodoList id: {self.id} name: {self.name}>"
  

class ToDo(db.Model):
  __tablename__ = "todos"
  id = db.Column(db.Integer, primary_key=1)
  description = db.Column(db.String(), nullable=0)
  completed = db.Column(db.Boolean, nullable=False, default=False)

  list_id = db.Column(db.Integer, db.ForeignKey('todo_lists.id'), nullable=0)

  def __repr__(self):
      return f"<ToDO ID: {self.id}, {self.description}>"

# db.create_all()


@app.route('/todos/create', methods=['POST'])
def create_todo():
    error = False
    body = {}
    try:
        description = request.get_json().get('description', '')
        list_id = request.get_json().get('list_id')
        todo = ToDo(description=description)
        todo.list_id = list_id

        db.session.add(todo)
        db.session.commit()
        body = {
            "id": todo.id,
            "description": todo.description
        }

    except:
        db.session.rollback()
        print(sys.exc_info())
        error = True

    finally:
        db.session.close()

    return abort(400) if error else jsonify(body)    


@app.route("/todos/<item_id>/set-completed", methods=["POST"])
def set_item_completed(item_id):
  try:
    completed = request.get_json().get("completed")
    item = ToDo.query.get(item_id)
    item.completed = completed
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())

  finally:
    db.session.close()

  return redirect(url_for("index"))

@app.route("/todos/<item_id>/delete", methods=["DELETE"])
def delete_item(item_id):
  try:
    ToDo.query.filter_by(id=item_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

  return jsonify({"success": True})


@app.route('/lists/<list_id>')
def get_list_items_by_id(list_id):
    data = ToDo.query.filter_by(list_id=list_id).order_by("id").all()
    lists = TodoList.query.all()
    active_list = TodoList.query.get(list_id)
    return render_template("index.html", data=data, lists=lists, active_list=active_list)

  
@app.route("/lists/new", methods=["POST"])
def create_new_list():
  try:
    new_list_name = request.get_json().get("name")
    lst = TodoList(name=new_list_name)

    db.session.add(lst)
    db.session.commit()

  except:
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for("index"))


@app.route("/")
def index():
  return redirect(url_for('get_list_items_by_id', list_id=1))

if __name__ == "__main__":
    app.run(debug=1)
