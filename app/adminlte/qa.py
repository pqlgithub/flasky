# -*- coding: utf-8 -*-
from flask import redirect, url_for, current_app, render_template, flash, request, abort
from flask_babelex import gettext
from flask_login import login_required
from . import adminlte
from .. import db
from app.models import Question, Solution
from app.forms import QuestionForm, SolutionForm

# TODO: 问题类别-增删改查


def load_common_data():
    """
    私有方法，装载共用数据
    """
    return {
        'top_menu': 'qa'
    }


@adminlte.route('/questions')
@adminlte.route('/questions/<int:page>')
def show_questions(page=1):
    per_page = request.args.get('per_page', 10, type=int)

    paginated_questions = Question.query.order_by(Question.id.desc()).paginate(page, per_page)

    return render_template('adminlte/qa/show_questions.html',
                           paginated_questions=paginated_questions,
                           sub_menu='questions',
                           **load_common_data())


@adminlte.route('/questions/create', methods=['GET', 'POST'])
def create_question():
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(
            pid=form.pid.data,
            name=form.name.data
        )
        db.session.add(question)
        db.session.commit()

        flash(gettext('Add Question is ok!'), 'success')
        return redirect(url_for('.show_questions'))
    else:
        current_app.logger.warn(form.errors)

    mode = 'create'
    paginated_questions = Question.query.filter_by(pid=0).order_by(Question.created_at.desc()).paginate(1, 1000)
    return render_template('adminlte/qa/create_edit_question.html',
                           form=form,
                           mode=mode,
                           paginated_questions=paginated_questions,
                           current_question=None,
                           sub_menu='questions',
                           **load_common_data())


@adminlte.route('/questions/<int:id>/edit', methods=['GET', 'POST'])
def edit_question(id):
    current_question = Question.query.get_or_404(id)

    form = QuestionForm()
    form.pid.choices = [(question.id, question.name) for question in Question.query.filter_by(pid=0)]
    if form.validate_on_submit():
        form.populate_obj(current_question)
        db.session.commit()
        flash(gettext('Edit Question is ok!'), 'success')
        return redirect(url_for('.show_questions'))

    mode = 'edit'
    paginated_questions = Question.query.filter_by(pid=0).order_by(Question.created_at.desc()).paginate(1, 1000)
    form.name.data = current_question.name
    form.pid.data = current_question.pid

    return render_template('adminlte/qa/create_edit_question.html',
                           form=form,
                           mode=mode,
                           paginated_questions=paginated_questions,
                           current_question=current_question,
                           sub_menu='questions',
                           **load_common_data())


@adminlte.route('/questions/delete', methods=['POST'])
def delete_question():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Disabled question is null!', 'danger')
        abort(404)

    try:
        for id in selected_ids:
            question = Question.query.get_or_404(int(id))
            db.session.delete(question)
        db.session.commit()
        flash('Delete question is ok!', 'success')
    except:
        db.session.rollback()
        flash('Delete question is fail!', 'danger')

    return redirect(url_for('.show_questions'))


# TODO:问题答案-增删改查
@adminlte.route('/solutions')
@adminlte.route('/solutions/<int:page>')
def show_solutions(page=1):
    per_page = request.args.get('per_page', 10, type=int)
    paginated_solutions = Solution.query.order_by(Solution.id.desc()).paginate(page, per_page)
    return render_template('adminlte/qa/show_solutions.html',
                           paginated_solutions=paginated_solutions,
                           sub_menu='solutions',
                           **load_common_data())


@adminlte.route('/solutions/create', methods=['GET', 'POST'])
def create_solution():
    form = SolutionForm()
    if form.validate_on_submit():
        solution = Solution(
            question_id=form.question_id.data,
            title=form.title.data,
            content=form.content.data
        )
        db.session.add(solution)
        db.session.commit()
        flash(gettext('Add Solution is ok!'), 'success')
        return redirect(url_for('.show_solutions'))
    else:
        current_app.logger.warn(form.errors)

    mode = 'create'
    paginated_questions = Question.query.filter(Question.pid != 0).order_by(Question.created_at.desc()).paginate(1, 1000)
    return render_template('adminlte/qa/create_edit_solution.html',
                           form=form,
                           mode=mode,
                           paginated_questions=paginated_questions,
                           current_solution=None,
                           sub_menu='solutions',
                           **load_common_data())


@adminlte.route('/solutions/<int:id>/edit', methods=['GET', 'POST'])
def edit_solution(id):
    current_solution = Solution.query.get_or_404(id)

    form = SolutionForm()
    if form.validate_on_submit():
        form.populate_obj(current_solution)
        db.session.commit()
        flash(gettext('Edit Solution is ok!'), 'success')
        return redirect(url_for('.show_solutions'))

    mode = 'edit'
    paginated_questions = Question.query.filter(Question.pid != 0).order_by(Question.created_at.desc()).paginate(1, 1000)
    form.question_id.data = current_solution.question_id
    form.title.data = current_solution.title
    form.content.data = current_solution.content

    return render_template('adminlte/qa/create_edit_solution.html',
                           form=form,
                           mode=mode,
                           paginated_questions=paginated_questions,
                           current_solution=current_solution,
                           sub_menu='solutions',
                           **load_common_data())


@adminlte.route('/solutions/delete', methods=['POST'])
def delete_solution():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Disabled solution is null!', 'danger')
        abort(404)

    try:
        for id in selected_ids:
            solution = Solution.query.get_or_404(int(id))
            db.session.delete(solution)
        db.session.commit()
        flash('Delete solution is ok!', 'success')
    except:
        db.session.rollback()
        flash('Delete solution is fail!', 'danger')

    return redirect(url_for('.show_solutions'))