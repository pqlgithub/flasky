# -*- coding: utf-8 -*-
import time
from app import db

__all__ = [
    'Counter'
]

class Counter(db.Model):
    """遍历计数器"""
    
    __tablename__ = 'counters'

    id = db.Column(db.Integer, primary_key=True)
    total_count = db.Column(db.Integer, default=1)

    @staticmethod
    def get_next_sequence():
        current_counter = Counter.query.first()
        if current_counter is not None:
            total_count = current_counter.total_count
            # 同步递增
            current_counter.total_count += 1
        else:
            total_count = 1
            new_counter = Counter(total_count=total_count)
            db.session.add(new_counter)

        return total_count

    
    @staticmethod
    def gen_product_sn(length=8):
        """生成产品sku"""
        serial_no = '8'
        serial_no += time.strftime('%m')
        rd = str(Counter.get_next_sequence())
        z = ''
        if len(rd) < length:
            for i in range(length - len(rd)):
                z += '0'

        return ''.join([serial_no, z, rd])

    
    @staticmethod
    def gen_store_sn(length=7):
        serial_no = '2'
        rd = str(Counter.get_next_sequence())
        z = ''
        if len(rd) < length:
            for i in range(length - len(rd)):
                z += '0'

        return ''.join([serial_no, z, rd])
    
    
    @staticmethod
    def gen_brand_sn(length=8):
        serial_no = '6'
        rd = str(Counter.get_next_sequence())
        z = ''
        if len(rd) < length:
            for i in range(length - len(rd)):
                z += '0'
    
        return ''.join([serial_no, z, rd])
    
    
    @staticmethod
    def gen_user_xid(length=8):
        serial_no = '1'
        serial_no += time.strftime('%d')
        rd = str(Counter.get_next_sequence())
        z = ''
        if len(rd) < length:
            for i in range(length - len(rd)):
                z += '0'

        return ''.join([serial_no, z, rd])

    
    def __repr__(self):
        return '<Counter {}>'.format(self.id)