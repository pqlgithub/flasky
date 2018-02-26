# -*- coding: utf-8 -*-
from flask import request, abort, g, current_app
from sqlalchemy.exc import IntegrityError
from app.models import Address, Place

from .. import db
from . import api
from .auth import auth
from .utils import *
    
    
@api.route('/address')
@auth.login_required
def get_addresses():
    """获取用户收货地址"""
    addresses = Address.query.filter_by(user_id=g.current_user.id).all()
    
    return full_response(R200_OK, [address.to_json() for address in addresses])


@api.route('/address/<string:rid>')
@auth.login_required
def get_address(rid):
    """获取某个收货地址"""
    address = Address.query.filter_by(user_id=g.current_user.id, serial_no=rid).first_or_404()
    
    return full_response(R200_OK, address.to_json())


@api.route('/address/is_default')
@auth.login_required
def get_default_address():
    """获取用户默认收货地址"""
    address = Address.query.filter_by(user_id=g.current_user.id, is_default=True).first_or_404()
    
    return full_response(R200_OK, address.to_json())


@api.route('/address', methods=['POST'])
@auth.login_required
def create_address():
    """新增用户收货地址"""
    if not request.json:
        abort(400)
    
    try:
        # 数据验证
        address = Address.from_json(request.json)
    
        address.master_uid = g.master_uid
        address.user_id = g.current_user.id
        address.serial_no = Address.make_unique_serial_no()
        
        db.session.add(address)
        db.session.commit()
    except IntegrityError as err:
        current_app.logger.error('Create address fail: {}'.format(str(err)))
    
        db.session.rollback()
        return status_response(custom_status('Create failed!', 400), False)

    return full_response(R201_CREATED, address.to_json())


@api.route('/address/<string:rid>', methods=['PUT'])
@auth.login_required
def update_address(rid):
    """更新用户收货地址"""
    address = Address.query.filter_by(user_id=g.current_user.id, serial_no=rid).first()
    if address is None:
        abort(404)

    try:
        json_address = request.json
        
        # 验证数据
        if not Address.validate_required_fields(json_address):
            return custom_response("Fields validate error!", 400, False)
        
        # 检测是否有默认地址
        is_default = json_address.get('is_default', False)
        if is_default:
            default_address_list = Address.query.filter_by(user_id=g.current_user.id, is_default=True).all()
            if default_address_list:
                for default_address in default_address_list:
                    # 如已有默认地址，则更新为非默认
                    if default_address.id != address.id:
                        default_address.is_default = False
        
        # 更新数据
        address.first_name = json_address.get('first_name', address.first_name)
        address.last_name = json_address.get('last_name', address.last_name)
        address.phone = json_address.get('phone', address.phone)
        address.mobile = json_address.get('mobile', address.mobile)
        address.province_id = json_address.get('province_id', address.province_id)
        address.city_id = json_address.get('city_id', address.city_id)
        address.town_id = json_address.get('town_id', address.town_id)
        address.area_id = json_address.get('area_id', address.area_id)
        address.street_address = json_address.get('street_address', address.street_address)
        address.street_address_two = json_address.get('street_address_two', address.street_address_two)
        address.zipcode = json_address.get('zipcode', address.zipcode)
        address.is_default = is_default
        
        db.session.commit()
    except IntegrityError as err:
        current_app.logger.error('Update address fail: {}'.format(str(err)))
        db.session.rollback()
        return custom_response('Update failed!', 400, False)
    
    return full_response(R200_OK, address.to_json())
    

@api.route('/address/<string:rid>/set_default', methods=['PUT'])
@auth.login_required
def mark_default_address(rid):
    """设置为默认地址"""
    address = Address.query.filter_by(user_id=g.current_user.id, serial_no=rid).first()
    if address is None:
        abort(404)

    default_address_list = Address.query.filter_by(user_id=g.current_user.id, is_default=True).all()
    if default_address_list:
        for default_address in default_address_list:
            # 如已有默认地址，则更新为非默认
            if default_address.id != address.id:
                default_address.is_default = False
                
    address.is_default = True
    
    db.session.commit()
    
    return status_response(R200_OK)
    

@api.route('/address/<string:rid>', methods=['DELETE'])
@auth.login_required
def delete_address(rid):
    """删除用户收货地址"""
    address = Address.query.filter_by(user_id=g.current_user.id, serial_no=rid).first_or_404()
    
    try:
        # 删除
        db.session.delete(address)
        db.session.commit()
    except:
        db.session.rollback()
        return custom_response('Delete failed!', 400, False)
    
    return status_response(R200_OK)


@api.route('/places')
@auth.login_required
def get_all_places():
    """获取全部省市区镇列表"""
    all_places = {}

    places = Place.query.filter_by(status=True).order_by(Place.layer.asc()).all()
    
    for place in places:
        key = '_'.join(['k', str(place.layer), str(place.pid)]) # k_layer_pid
        if key not in all_places.keys():
            all_places[key] = [place.to_json()]
        else:
            all_places[key].append(place.to_json())
    
    return full_response(R200_OK, all_places)


@api.route('/places/provinces')
@auth.login_required
def get_provinces():
    """获取省级列表"""
    provinces = Place.provinces()
    
    return full_response(R200_OK, [p.to_json() for p in provinces])


@api.route('/places/cities')
@api.route('/places/<int:pid>/cities')
@auth.login_required
def get_cities(pid=0):
    """获取市级列表"""
    cities = Place.cities(pid)
    
    return full_response(R200_OK, [c.to_json() for c in cities])


@api.route('/places/towns')
@api.route('/places/<int:pid>/towns')
@auth.login_required
def get_towns(pid=0):
    """获取区镇级列表"""
    towns = Place.towns(pid)

    return full_response(R200_OK, [t.to_json() for t in towns])


@api.route('/places/areas')
@api.route('/places/<int:pid>/areas')
@auth.login_required
def get_areas(pid=0):
    """获取村或区域列表"""
    areas = Place.areas(pid)

    return full_response(R200_OK, [a.to_json() for a in areas])

