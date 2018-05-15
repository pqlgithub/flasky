# -*- coding: utf-8 -*-
from flask import g, session, current_app, request, redirect, url_for, render_template
from . import qa
from app.api_1_0.utils import *

from app.models import Question, Solution


@qa.route('/index')
def help_center():
    """帮助中心"""
    pass


@qa.route('/questions')
def show_questions():
    """问题列表"""
    questions = Question.query.filter_by(pid=0).all()
    for question in questions:
        question.sub_questions = Question.query.filter_by(pid=question.id).all()

    return render_template('web/questions.html',
                           active_menu='questions',
                           questions=questions)


@qa.route('/questions/<int:pid>')
def show_sub_questions(pid):
    """二级问题列表"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)

    question = Question.query.get(pid)
    if question is None:
        return full_response(R400_BADREQUEST, data={'err': '参数错误'}, success=False)

    pagination = Question.query.filter_by(pid=pid).paginate(page, per_page)
    sub_questions = pagination.items
    return full_response(R200_OK, {
        'sub_questions': [question.to_json() for question in sub_questions]
    })


@qa.route('/solutions/<int:question_id>')
def show_solution(question_id):
    """解决答案"""
    solution = Solution.query.get(question_id=question_id)
    if solution is None:
        return full_response(R400_BADREQUEST, data={'err': '参数错误'}, success=False)

    return full_response(R200_OK, {
        'solution': solution.to_json()
    })
