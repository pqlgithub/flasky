# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request, current_app
from flask_babelex import gettext, lazy_gettext
from . import adminlte
from .. import db
from app.models import Place, Country
from app.forms import PlaceForm, CountryForm, EditCountryForm
from ..utils import full_response, custom_status, R200_OK, R201_CREATED, R400_BADREQUEST, Master, custom_response

def load_common_data():
    """
    私有方法，装载共用数据
    """
    return {
        'top_menu': 'address'
    }

@adminlte.route('/places')
@adminlte.route('/places/<int:page>')
def show_places(page=1):
    """省市区镇列表"""
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('s', 0, type=int)
    layer = request.args.get('layer', type=int)
    
    if not status:
        query = Place.query
    else:
        query = Place.query.filter_by(status=status)
    
    paginated_places = query.order_by(Place.created_at.desc()).paginate(page, per_page)

    return render_template('adminlte/places/show_list.html',
                           paginated_places=paginated_places,
                           status=status,
                           layer=layer,
                           sub_menu='places',
                           **load_common_data())


@adminlte.route('/places/create', methods=['GET', 'POST'])
def create_place():
    form = PlaceForm()
    form.country_id.choices = [(country.id, country.name) for country in Country.query.filter_by(status=True).all()]
    if form.validate_on_submit():
        pid = form.pid.data
        if pid:
            parent_node = Place.query.get_or_404(int(pid))
            next_layer = parent_node.layer + 1
        else:
            pid = 0
            next_layer = 1
        
        # 添加下一级
        place = Place(
            country_id=form.country_id.data,
            name=form.name.data,
            pid=pid,
            layer=next_layer,
            status=form.status.data
        )
        db.session.add(place)
        db.session.commit()
        
        flash(gettext('Add Place is ok!'), 'success')
        
        return redirect(url_for('.show_places'))
    else:
        current_app.logger.warn(form.errors)
    
    mode = 'create'
    parent_nodes = None
    pid = request.args.get('pid', type=int)
    if pid:
        form.pid.data = pid
        # 获取父级
        parent_nodes = Place.find_parent(pid, tree=[])
        
    return render_template('adminlte/places/create_and_edit.html',
                           form=form,
                           mode=mode,
                           sub_menu='places',
                           parent_nodes=parent_nodes,
                           **load_common_data())

@adminlte.route('/places/<int:id>/edit', methods=['GET', 'POST'])
def edit_place(id):
    current_place = Place.query.get_or_404(id)
    
    form = PlaceForm()
    form.country_id.choices = [(country.id, country.name) for country in Country.query.filter_by(status=True).all()]
    if form.validate_on_submit():
        form.populate_obj(current_place)
        
        db.session.commit()

        flash(gettext('Edit Place is ok!'), 'success')

        return redirect(url_for('.show_places'))
    
    mode = 'edit'
    # 获取父级
    parent_nodes = Place.find_parent(current_place.pid, tree=[])
    
    form.name.data = current_place.name
    form.pid.data = current_place.pid
    form.sort_by.data = current_place.sort_by
    form.status.data = current_place.status
    
    return render_template('adminlte/places/create_and_edit.html',
                           form=form,
                           mode=mode,
                           sub_menu='places',
                           parent_nodes=parent_nodes,
                           **load_common_data())


@adminlte.route('/places/delete', methods=['POST'])
def delete_place():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Delete place is null!', 'danger')
        abort(404)
    
    try:
        for id in selected_ids:
            place = Place.query.get_or_404(int(id))
            db.session.delete(place)
        
        db.session.commit()
        
        flash('Delete place is ok!', 'success')
    except:
        db.session.rollback()
        flash('Delete place is fail!', 'danger')
    
    return redirect(url_for('.show_places'))


@adminlte.route('/countries')
@adminlte.route('/countries/<int:page>')
def show_countries(page=1):
    per_page = request.args.get('per_page', 10, type=int)

    paginated_countries = Country.query.order_by(Country.id.asc()).paginate(page, per_page)

    if paginated_countries:
        paginated_countries.offset_start = 1 if page == 1 else (page - 1) * per_page
        paginated_countries.offset_end = paginated_countries.offset_start + len(paginated_countries.items) - 1

    return render_template('adminlte/countries/show_countries.html',
                           paginated_countries=paginated_countries,
                           sub_menu='countries',
                           **load_common_data())


@adminlte.route('/countries/create', methods=['GET', 'POST'])
def create_country():
    form = CountryForm()
    if form.validate_on_submit():
        try:
            country = Country(
                name=form.name.data,
                code=form.code.data,
                code2=form.code2.data,
                en_name=form.en_name.data,
                status=form.status.data
            )
            db.session.add(country)
        
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            flash(gettext('Add Country is fail: %s!' % ex) , 'danger')
            
            return redirect(url_for('.create_country'))

        flash(gettext('Add country is ok!'), 'success')

        return redirect(url_for('.show_countries'))
    else:
        current_app.logger.warn(form.errors)
    
    mode = 'create'
    return render_template('adminlte/countries/create_and_edit.html',
                           form=form,
                           mode=mode,
                           sub_menu='countries',
                           **load_common_data())


@adminlte.route('/countries/<int:id>/edit', methods=['GET', 'POST'])
def edit_country(id):
    country = Country.query.get_or_404(id)
    form = EditCountryForm(country)
    if form.validate_on_submit():
        form.populate_obj(country)
        
        db.session.commit()

        flash(gettext('Edit country is ok!'), 'success')
        return redirect(url_for('.show_countries'))

    mode = 'edit'

    # populate data for form
    form.name.data = country.name
    form.en_name.data = country.en_name
    form.code.data = country.code
    form.code2.data = country.code2
    form.status.data = country.status

    return render_template('adminlte/countries/create_and_edit.html',
                           form=form,
                           country=country,
                           mode=mode,
                           sub_menu='countries',
                           **load_common_data())


@adminlte.route('/countries/delete', methods=['POST'])
def delete_country():
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash(gettext('Delete country is null!'), 'danger')
        abort(404)
    
    try:
        for id in selected_ids:
            country = Country.query.get_or_404(int(id))
            db.session.delete(country)

        db.session.commit()

        flash(gettext('Delete country is ok!'), 'success')
    except:
        db.session.rollback()
        flash(gettext('Delete country is error!!!'), 'danger')

    return redirect(url_for('.show_countries'))
