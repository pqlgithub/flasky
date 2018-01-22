# -*- coding: utf-8 -*-

from flask import current_app
from app import db
from app.models import Currency, User, Ability, Directory, Asset, Supplier, Express
from app.constant import DEFAULT_ACLIST, DEFAULT_DIRECTORY, DEFAULT_ASSET, DEFAULT_SUPPLIER, DEFAULT_EXPRESS


class InitialSystem(object):
	"""
	系统初始化，配置系统默认数据
	"""

	@staticmethod
	def init_currency():
		"""初始化默认币种"""
		pass

	@staticmethod
	def init_admin():
		"""初始化系统管理员"""

		for email in current_app.config['ADMINS']:
			if User.query.filter_by(email=email, is_admin=True).first():
				print('System user: %s already initial, exit!' % email)

				continue

			user = User()

			user.email = email
			user.username = email.split('@')[0]
			user.password = 'Mic#2009?!'
			user.time_zone = 'zh'
			user.confirmed = True
			user.is_admin = True

			db.session.add(user)

		db.session.commit()

		print('System user is initial!')

	@staticmethod
	def init_acl():
		"""初始化权限管理"""

		# 检测是否已安装数据
		total_count = Ability.query.count()
		if total_count:
			print('Ability is initial, exit!')
			return None

		# 安装权限列表
		for acl in DEFAULT_ACLIST:
			ability = Ability(
				name=acl[0],
				title=acl[1]
			)
			db.session.add(ability)

		db.session.commit()

	@staticmethod
	def init_directory():
		"""初始化默认目录"""

		default_name = DEFAULT_DIRECTORY['name']
		if Directory.query.filter_by(is_default=True).first():
			print('Default directory already initial, exit!')
			return None

		default_directory = Directory(
			name=default_name,
			is_default=True
		)
		db.session.add(default_directory)
		db.session.commit()

		print('Default directory is initial!')

	@staticmethod
	def init_asset():
		"""初始化附件图片"""

		if Asset.query.filter_by(is_default=True).first():
			print('Default asset already initial, exit!')
			return None

		default_directory = Directory.query.filter_by(is_default=True).first()
		default_asset = Asset(directory=default_directory, **DEFAULT_ASSET)

		db.session.add(default_asset)
		db.session.commit()

		print('Default asset is initial!')

	@staticmethod
	def init_supplier():
		"""初始化默认供应商"""

		if Supplier.query.filter_by(is_default=True).first():
			print('Default supplier already initial, exit!')
			return None

		default_supplier = Supplier(
			**DEFAULT_SUPPLIER
		)

		db.session.add(default_supplier)
		db.session.commit()

		print('Default supplier is initial!')

	@staticmethod
	def init_express():
		"""初始化默认物流公司"""

		if Express.query.filter_by(is_default=True).first():
			print('Default express already initial, exit!')
			return None

		default_express = Express(**DEFAULT_EXPRESS)

		db.session.add(default_express)
		db.session.commit()

		print('Default express is initial!')
