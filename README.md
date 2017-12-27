# micku
Erp for mic

## 系统要求：
- Python 3.6+、Flask 1.0+、virtualenv3.5
- Mysql 5.0+
- Nginx/1.8.0
- gevent (1.1.2)
- gunicorn (19.6.0)



## 功能特性：
- 支持多语言
- 支持多账户管理

## 安装要求：

#### 添加语言支持
    ./tr_compile.py
    ./tr_init.py en
    ./tr_update.py #有更新时


## Gunicorn进程管理（生成环境）

    sudo gunicorn -c deploy/gun.py manage:app -u apps


### Python3.6下支持Supervisor管理
使用**virtualenv**安装创建独立的Python环境

项目运行于 `Python3` 环境下：

    virtualenv py3env --python=python3

启动虚拟环境：

    source py3env/bin/activate

退出虚拟环境：

    deactivate
    
Supervisor运行于 `Python2.7` 环境下：

    virtualenv py2env --python=python2.7
    
    pip install supervisor
    
    echo_supervisord_conf > supervisord.conf
    
配置文件中添加：

    [program:gunicorn]
    directory=/opt/project/mishoply
    command=/opt/project/mishoply/venv/bin/gunicorn -c /opt/project/mishoply/deploy/gun.py manage:app
    autostart=true
    startsecs=10
    autorestart=true
    startretries=20
    user=apps

**运行要加上自己环境的虚拟目录**

启动Supervisord:

    supervisord -c supervisord.conf
    
关闭Supervisor:

    supervisorctl -c supervisor.conf shutdown
    
重新载入配置：

    supervisorctl -c supervisor.conf reload
    
查看Supervisor的状态:

    supervisorctl -c supervisor.conf status


### 文献资料参考：

* [flask+gunicorn+supervisorn+nginx项目部署](https://clayandmore.github.io/2017/03/19/flask+gunicorn+supervisorn+nginx%E9%A1%B9%E7%9B%AE%E9%83%A8%E7%BD%B2/)

