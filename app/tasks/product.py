# -*- coding: utf-8 -*-
from flask import current_app
from app.extensions import fsk_celery

from app import db
from app.models import Product, SearchHistory

FAIL = 'FAIL'
SKIP = 'SKIP'
SUCCESS = 'SUCCESS'


@fsk_celery.task(name='product.update_search_history')
def update_search_history(qk, uid, total_count=0, user_id=0):
    """新增或更新搜索历史记录"""

    current_app.logger.warn('Task: update search[%s] history' % qk)

    history = SearchHistory.query.filter_by(master_uid=uid, query_word=qk).first()
    if history is None:
        # 新增
        history = SearchHistory(
            master_uid=uid,
            user_id=user_id,
            query_word=qk,
            total_count=total_count
        )
        db.session.add(history)
    else:
        history.total_count = total_count
        history.search_times += 1

    db.session.commit()

    return SUCCESS
