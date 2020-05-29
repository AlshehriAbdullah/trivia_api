import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
from models import setup_db, Question, Category


db = SQLAlchemy()
QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    current_question = questions[start:end] 

    return current_question


def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app)


  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-type, Authorization')
    response.headers.add('Access-Control-Allow-Headers', 'GET, POST, PATCH, DELETE, OPTIONS')
    return response


  @app.route('/categories')
  def get_categories():
    categories = Category.query.all()
    categ_format = {category.id: category.type for category in categories}
    if not categories:
      abort(404)

    return jsonify({
            'success':True,
            'categories': categ_format
        })


  @app.route('/questions')
  def get_questions():
    questions = Question.query.all()
    current_qts = paginate_questions(request, questions)
    categories = Category.query.all()
    categ_format ={category.id: category.type for category in categories}
    current_category = []
    for categ in current_qts:
      current_category.append(
        db.session.query(Category.type).filter(
          Category.id == categ['category']
        ).all()
      )
    if not current_qts:
      abort(404)

    return jsonify({
            'success':True,
            'questions': current_qts,
            'categories': categ_format,
            'current_category': current_category,
            'total_questions': len(Question.query.all())
    })


  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def Delete_Qts(question_id):
    try:
      questions = Question.query.get(question_id)
      if questions is None:
        abort(404)
      questions.delete()
      return jsonify({
            'success': True,
            'deleted': questions.id
          })
    except:
        abort(422)


  @app.route('/questions', methods=['POST'])
  def create_questions():
    try:
      body = request.get_json()
      question = body.get('question', None)
      answer = body.get('answer', None)
      category = body.get('category', None)
      difficulty = body.get('difficulty', None)

      question = Question(
        question=question, answer=answer, category=category, difficulty=difficulty
      )
      question.insert()
      questions = Question.query.order_by(Question.id).all()
      current_qts = paginate_questions(request, questions)
      return jsonify({
                'success': True,
                'questions': current_qts,
                'created': question.id,
                'total_questions': len(questions)
            })
    except:
      abort(422)


  @app.route('/questions/search', methods=['POST'])
  def search_questions():
    try:
      body = request.get_json()
      search = body.get('searchTerm', None)
      questions = Question.query.order_by(Question.id).filter(Question.question.ilike('%'+search+'%')).all()
      current_qts = paginate_questions(request, questions)
      current_category = []
      for categ in current_qts:
        current_category.append(
          db.session.query(Category.type).filter(
            Category.id == categ['category']
          ).all()
        )
        
        
      return jsonify({
                'success': True,
                'questions': current_qts,
                'current_category': current_category,
                'total_questions': len(questions)
            })
    except:
      abort(422)


  @app.route('/categories/<int:category_id>/questions')
  def quest_catgo(category_id):
    questions = Question.query.filter(Question.category == category_id).all()
    current_qts = paginate_questions(request, questions)
    if len(current_qts) == 0:
      abort(404)
    return jsonify({
      'success':True,
      'questions': current_qts,
      'current_category': category_id,
      'total_questions': len(questions)
    })


  @app.route('/quizzes', methods=['POST'])
  def get_quiz_questions():
      body = request.get_json()
      previous_questions = body.get('previous_questions', None)
      quiz_category = body.get('quiz_category', None)
      categ_id = int(quiz_category['id'])
      try:
          if categ_id == 0:
              questions = Question.query.filter(~Question.id.in_(previous_questions)).all()
          else:
              questions = Question.query.filter( Question.category == categ_id, ~Question.id.in_(previous_questions)).all()
          if questions:
              random_question = questions[random.randint(0, len(questions))]
              random_question_format = random_question.format()
          else:
              question = False
          return jsonify({
              'success': True,
               'previous_questions':previous_questions,
               'question':random_question_format,
               'categ_id':categ_id
          })
  
      except:
          abort(404)

  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({
        "success": False, 
        "error": 400,
        "message": 'issue with the request'
            }), 400

  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False, 
      "error": 404,
      "message": 'page could not found'
            }), 404
        
  @app.errorhandler(405)
  def not_allowed(error):
      return jsonify({
          "success": False, 
          "error": 405,
          "message": 'method not allowed'
            }), 405

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
        "success": False, 
        "error": 422,
        "message": 'unable to be processed'
            }), 422

  
  return app

    