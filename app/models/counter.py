# -*- coding: utf-8 -*-
import time, random, string
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
        if current_counter:
            total_count = current_counter.total_count + 1
            
            # 同步递增
            current_counter.total_count += 1
        else:
            total_count = 1010
            new_counter = Counter(total_count=total_count)
            db.session.add(new_counter)
        
        return total_count

    
    def __repr__(self):
        return '<Counter {}>'.format(self.id)