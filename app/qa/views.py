# -*- coding: utf-8 -*-
from flask import g, session, current_app, request, redirect, url_for, render_template, abort
from flask_sqlalchemy import Pagination
from . import qa
from .. import db
from app.api_1_0.utils import *

from app.models import Question, Solution


@qa.route('/index')
def help_center():
    """帮助中心"""
    pass


@qa.route('/solutions')
def show_solutions():
    """二级问题分类下所有的Solution"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    question_id = request.values.get('question_id', 0, type=int)

    question = Question.query.get(question_id)
    if question is None:
        return status_response(False, R400_BADREQUEST)

    solutions = Solution.query.filter_by(question_id=question_id).all()
    # 构造分页
    total_count = len(solutions)
    if page == 1:
        start = 0
    else:
        start = (page - 1) * per_page
    end = start + per_page

    paginated_solutions = solutions[start:end]
    pagination = Pagination(query=None, page=page, per_page=per_page, total=total_count, items=None)
    return render_template('qa/show_list.html',
                           paginated_solutions=paginated_solutions,
                           pagination=pagination,
                           question_id=question_id,
                           question_name=question.name)


@qa.route('/solution')
def show_solution():
    """解决答案"""
    solution_id = request.values.get('solution_id', 0, type=int)
    solution = Solution.query.get_or_404(solution_id)

    return render_template('qa/show_solution.html',
                           solution=solution)


@qa.route('/solution/useful', methods=['POST'])
def update_useful():
    """解答有用，更新有用的数量"""
    solution_id = request.values.get('solution_id', 0, type=int)
    solution = Solution.query.get(solution_id)
    if solution is None:
        return status_response(False, R400_BADREQUEST)

    solution.useful_count += 1
    db.session.add(solution)
    db.session.commit()
    return full_response(R200_OK, None)


@qa.route('/solution/useless', methods=['POST'])
def update_useless():
    """解答无用，更新无用的数量和无用原因"""
    solution_id = request.values.get('solution_id')
    reason = request.values.get('reason')
    solution = Solution.query.get(solution_id)

    if solution is None:
        return status_response(False, R400_BADREQUEST)

    solution.useless_count += 1
    if '1' == reason:
        solution.cause_describe += 1
    elif '2' == reason:
        solution.cause_product += 1
    elif '3' == reason:
        solution.cause_content_err += 1
    elif '4' == reason:
        solution.cause_operation += 1

    db.session.add(solution)
    db.session.commit()
    return full_response(R200_OK, None)


@qa.route('/solutions/search', methods=['GET'])
def search_solutions(page=1):
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    qk = request.values.get('qk')
    qk = qk.strip()
    if not qk:
        return render_template('qa/search_result.html')

    builder = Solution.query.whoosh_search(qk, like=True)
    solutions = builder.order_by(Solution.id.desc()).all()
    # 构造分页
    total_count = len(solutions)
    if page == 1:
        start = 0
    else:
        start = (page - 1) * per_page
    end = start + per_page
    current_app.logger.debug('total count [%d], start [%d], per_page [%d]' % (total_count, start, per_page))
    paginated_solutions = solutions[start:end]
    pagination = Pagination(query=None, page=page, per_page=per_page, total=total_count, items=None)

    return render_template('qa/search_result.html',
                            qk=qk,
                            total_count=total_count,
                            paginated_solutions=paginated_solutions,
                            pagination=pagination)
