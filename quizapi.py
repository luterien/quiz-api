from flask import Flask, json, jsonify, request
from flask.ext.restful import Resource, Api, reqparse, abort

from functools import wraps

import sqlite3

app = Flask(__name__)
api = Api(app)


BASE_ROUTE = "/quizapp/api/1.0/"
DATABASE = "quizapp.db"

category_fields = ["id", "name"]
quiz_fields = ["id", "title", "level", "category_id"]
question_fields = ["id", "content", "score", "quiz_id"]
option_fields = ["id", "content", "is_correct"]

def db_init():
    connection = sqlite3.connect(DATABASE)
    cur = connection.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS quizes (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, level INTEGER, category_id INTEGER, FOREIGN KEY(category_id) references categories(id))')
    cur.execute('CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, score INTEGER, quiz_id INTEGER, FOREIGN KEY(quiz_id) references quizes(id))')
    cur.execute('CREATE TABLE IF NOT EXISTS options (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, is_correct INTEGER, question_id INTEGER, FOREIGN KEY(question_id) references questions(id))')
    connection.commit()
    print "db created"
    connection.close()


# Category resources

category_parser = reqparse.RequestParser()
category_parser.add_argument('name', type=str, required=True)


class Category(Resource):

    def get(self, category_id):
        s = run_query("SELECT * FROM categories WHERE id = ?", [category_id], True)
        return jsonify(jsonize(category_fields, s))

    # no-db-implementation-yet
    def put(self, category_id):
        d = request.form["data"]
        print d
        return categories[category_id]


# OK
class CategoryList(Resource):

    def get(self):
        rows = run_query("SELECT * FROM categories")
        print rows
        return jsonify([(row[0], jsonize(category_fields, row, ["id"])) for row in rows])

    def post(self):
        args = category_parser.parse_args()
        id = add_to_db("INSERT INTO categories (name) VALUES (?)", [args["name"]])
        return id, 201


api.add_resource(Category, BASE_ROUTE + "categories/<string:category_id>")
api.add_resource(CategoryList, BASE_ROUTE + "categories")


# Quiz resources

quiz_parser = reqparse.RequestParser()
quiz_parser.add_argument('title', type=str, required=True)
quiz_parser.add_argument('level', type=int, required=True)
quiz_parser.add_argument('category_id', type=int, required=True)

class Quiz(Resource):

    def get(self, quiz_id):
        s = run_query("SELECT * FROM quizes WHERE id = ?", [quiz_id], True)
        return jsonify(jsonize(quiz_fields, s))

    # no-db-implementation-yet
    def put(self, quiz_id):
        quizes[quiz_id] = request.form["data"]
        return quizes[quiz_id]


class QuizList(Resource):

    def get(self):
        rows = run_query("SELECT * FROM quizes")
        return jsonify([(row[0], jsonize(quiz_fields, row, ["id"])) for row in rows])

    def post(self):
        args = quiz_parser.parse_args()
        id = add_to_db("INSERT INTO quizes (title, level, category_id) VALUES (?, ?, ?)", [args["title"], args["level"], args["category_id"]])
        return id, 201

api.add_resource(Quiz, BASE_ROUTE + "quizes/<string:quiz_id>")
api.add_resource(QuizList, BASE_ROUTE + "quizes")


# Question resources

question_parser = reqparse.RequestParser()
question_parser.add_argument('text', type=str, required=True)
question_parser.add_argument('score', type=int, required=True)
question_parser.add_argument('options', type=str, required=True, action="append")
question_parser.add_argument('answer', type=str, required=True)
question_parser.add_argument('quiz_id', type=int, required=True)

class Question(Resource):

    def get(self, question_id):
        question = run_query("SELECT * FROM questions WHERE id = ?", [question_id], True)
        question_as_dict = jsonize(quiz_fields, question)
        # add options
        options = run_query("SELECT * FROM options WHERE question_id = ?", [question_id])
        options_list = [(option[0], jsonize(option_fields, option, ["id"])) for option in options]

        question_as_dict["options"] = dict(options_list)

        return jsonify(question_as_dict)

    def put(self, question_id):
        questions[question_id] = request.form["data"]
        return questions[question_id]


class QuestionList(Resource):

    def get(self):
        rows = run_query("SELECT * FROM questions")
        return jsonify([(row[0], jsonize(quiz_fields, row, ["id"])) for row in rows])

    def post(self):
        args = question_parser.parse_args()
        id = add_to_db("INSERT INTO questions (content, score, quiz_id) VALUES (?, ?, ?)", [args["text"], args["score"], args["quiz_id"]])
        # add options
        for option in args["options"]:
            add_to_db("INSERT INTO options (content, is_correct, question_id) VALUES (?, ?, ?)", [option, 0, id])
        # add correct answer
        add_to_db("INSERT INTO options (content, is_correct, question_id) VALUES (?, ?, ?)", [args["answer"], 1, id])

        return id, 201

api.add_resource(Question, BASE_ROUTE + "questions/<string:question_id>")
api.add_resource(QuestionList, BASE_ROUTE + "questions")


# Database operations

def connect_db():
    db_init()
    return sqlite3.connect(DATABASE)


def run_query(query, args=(), one=False):
    connection = connect_db()
    cur = connection.cursor().execute(query, args)
    if one:
        rows = cur.fetchone()
    else:
        rows = cur.fetchall()
    connection.close()
    return rows


def add_to_db(query, args=()):
    connection = connect_db()
    cur = connection.cursor().execute(query, args)
    connection.commit()
    id = cur.lastrowid
    connection.close()
    return id


# helpers

def jsonize(keys, values, exclude=[]):
    values = list(values)
    return dict([(keys[i], values[i]) for i in range(0, len(keys)) if not keys[i] in exclude])


if __name__ == "__main__":
    app.run(debug=True)