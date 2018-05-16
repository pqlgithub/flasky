# -*- coding: utf-8 -*-
from flask import g, session, current_app, request, redirect, url_for, render_template
from flask_sqlalchemy import Pagination
from . import qa
from .. import db
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
        return status_response(False, R400_BADREQUEST)

    pagination = Question.query.filter_by(pid=pid).paginate(page, per_page)
    sub_questions = pagination.items
    return full_response(R200_OK, {
        'sub_questions': [question.to_json() for question in sub_questions]
    }, success=True)


@qa.route('/solutions/<int:question_id>')
def show_solution(question_id):
    """解决答案"""
    solution = Solution.query.filter_by(question_id=question_id)
    if solution is None:
        return status_response(False, R400_BADREQUEST)

    return full_response(R200_OK, {
        'solution': solution.to_json()
    }, success=True)


@qa.route('/solutions/<int:solution_id>/useful')
def update_useful(solution_id):
    """解答有用，更新有用的数量"""
    solution = Solution.query.get(solution_id)
    if solution is None:
        return status_response(False, R400_BADREQUEST)

    solution.useful_count += 1
    db.session.add(solution)
    db.session.commit()
    return full_response(R200_OK, success=True)


@qa.route('/solutions/<int:solution_id>/useless')
def update_useless(solution_id):
    """解答无用，更新无用的数量和无用原因"""
    solution = Solution.query.get(solution_id)
    useless_reason = request.values.get('useless_reason')

    if solution is None:
        return status_response(False, R400_BADREQUEST)

    solution.useless_count += 1
    if 'cause_describe' == useless_reason:
        solution.cause_describe += 1
    elif 'cause_product' == useless_reason:
        solution.cause_product += 1
    elif 'cause_content_err' == useless_reason:
        solution.cause_content_err += 1
    elif 'cause_operation' == useless_reason:
        solution.cause_operation += 1
    else:
        solution.cause_describe += 1
    db.session.add(solution)
    db.session.commit()
    return full_response(R200_OK, success=True)


@qa.route('/solutions/search')
def search():
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    qk = request.values.get('qk')
    qk = qk.strip()
    builder = Solution.query.whoosh_search(qk, like=True)
    solutions = builder.order_by(Solution.id.desc()).all()
    # 构造分页
    total_count = builder.count()
    if page == 1:
        start = 0
    else:
        start = (page - 1) * per_page
    end = start + per_page
    current_app.logger.debug('total count [%d], start [%d], per_page [%d]' % (total_count, start, per_page))
    paginated_solutions = solutions[start:end]
    pagination = Pagination(query=None, page=page, per_page=per_page, total=total_count, items=None)
    solutions = [solution.to_json() for solution in solutions]
    return full_response(R200_OK, {
        'total_count': total_count,
        'solutions': solutions,
        'pagination': pagination
    }, success=True)